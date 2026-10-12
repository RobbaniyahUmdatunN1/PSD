"""Training & perbandingan model klasifikasi LULC.

Alur:
  1. baca data/training_samples.csv (hasil GEE), bersihkan, seimbangkan jumlah titik per kelas
  2. split TRAIN/TEST PER POLIGON (bukan per piksel) agar tidak ada kebocoran spasial
  3. latih beberapa model, evaluasi dengan GroupKFold-CV (train) dan data uji (test)
  4. pilih model terbaik, simpan model + hasil (results/results.json + grafik)
  5. eksperimen jumlah data latih (learning curve)

Pemakaian:  python train_models.py [--csv data/training_samples.csv] [--seed 42]
"""
import argparse, json, time, warnings
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import (accuracy_score, f1_score, cohen_kappa_score,
                             classification_report, confusion_matrix)
from sklearn.model_selection import GroupKFold, cross_val_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

import config as C

warnings.filterwarnings("ignore")


def build_models(seed):
    models = {
        "Random Forest (baseline)": RandomForestClassifier(n_estimators=300, n_jobs=-1, random_state=seed),
        "Extra Trees": ExtraTreesClassifier(n_estimators=300, n_jobs=-1, random_state=seed),
        "HistGradientBoosting": HistGradientBoostingClassifier(random_state=seed),
        "SVM (RBF)": make_pipeline(StandardScaler(), SVC(C=10, gamma="scale", random_state=seed)),
        "KNN (k=7)": make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=7, n_jobs=-1)),
        "MLP (Neural Net)": make_pipeline(StandardScaler(), MLPClassifier(
            hidden_layer_sizes=(128, 64), max_iter=400, early_stopping=True, random_state=seed)),
    }
    try:
        from xgboost import XGBClassifier
        models["XGBoost"] = XGBClassifier(n_estimators=400, max_depth=6, learning_rate=0.08,
                                          subsample=0.8, colsample_bytree=0.8, n_jobs=-1,
                                          random_state=seed, eval_metric="mlogloss")
    except ImportError:
        print("[!] xgboost tidak terpasang, dilewati")
    try:
        from lightgbm import LGBMClassifier
        models["LightGBM"] = LGBMClassifier(n_estimators=400, learning_rate=0.08, num_leaves=31,
                                            subsample=0.8, colsample_bytree=0.8, n_jobs=-1,
                                            random_state=seed, verbose=-1)
    except ImportError:
        print("[!] lightgbm tidak terpasang, dilewati")
    return models


def split_by_polygon(df, test_frac, seed):
    """Pisahkan poligon (bukan piksel) per kelas -> train/test."""
    rng = np.random.RandomState(seed)
    test_polys = []
    for _, g in df.groupby("class_id"):
        ids = np.array(sorted(g["poly_id"].unique()))
        rng.shuffle(ids)
        n_test = max(1, int(round(test_frac * len(ids))))
        test_polys += list(ids[:n_test])
    is_test = df["poly_id"].isin(test_polys)
    return df[~is_test].copy(), df[is_test].copy()


def balance(df, seed, n=None):
    """Samakan jumlah titik per kelas (downsample ke kelas terkecil)."""
    n = n or df["class_id"].value_counts().min()
    parts = [g.sample(n=min(n, len(g)), random_state=seed) for _, g in df.groupby("class_id")]
    return pd.concat(parts).reset_index(drop=True)


def counts(df):
    vc = df["class_id"].value_counts().sort_index()
    return {C.CLASS_NAMES[k]: int(v) for k, v in vc.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(C.SAMPLES_CSV))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--test-frac", type=float, default=0.2)
    ap.add_argument("--no-balance", action="store_true", help="jangan seimbangkan jumlah titik per kelas")
    args = ap.parse_args()
    C.RESULT_DIR.mkdir(exist_ok=True); C.MODEL_DIR.mkdir(exist_ok=True)

    # ---------- 1. data
    raw = pd.read_csv(args.csv)
    need = ["class_id", "class_name", "poly_id"] + C.FEATURES
    missing = [c for c in need if c not in raw.columns]
    if missing:
        raise SystemExit(f"Kolom tidak ada di CSV: {missing}")
    n_raw = len(raw)
    df = raw[need].replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)
    df = C.clip_features(df)
    print(f"Data mentah {n_raw} baris -> bersih {len(df)} baris")
    print("Per kelas (sebelum seimbang):", counts(df))
    n_clean_counts = counts(df)
    if not args.no_balance:
        df = balance(df, args.seed)

    # ---------- 2. split per poligon
    train, test = split_by_polygon(df, args.test_frac, args.seed)
    print(f"TRAIN {len(train)} | TEST {len(test)} | kelas {df['class_id'].nunique()}")
    Xtr, ytr = train[C.FEATURES].values, train["class_id"].values - 1   # label 0..K-1
    Xte, yte = test[C.FEATURES].values, test["class_id"].values - 1
    gtr = train["poly_id"].values
    labels = list(range(len(C.CLASS_IDS)))
    names = [C.CLASS_NAMES[i + 1] for i in labels]

    # ---------- 3. bandingkan model
    rows, fitted = [], {}
    cv = GroupKFold(n_splits=5)
    for name, model in build_models(args.seed).items():
        t0 = time.time()
        cv_scores = cross_val_score(clone(model), Xtr, ytr, groups=gtr, cv=cv, scoring="accuracy", n_jobs=1)
        model.fit(Xtr, ytr)
        pred = model.predict(Xte)
        row = {"model": name,
               "cv_acc_mean": float(cv_scores.mean()), "cv_acc_std": float(cv_scores.std()),
               "test_acc": float(accuracy_score(yte, pred)),
               "test_f1_macro": float(f1_score(yte, pred, average="macro")),
               "test_kappa": float(cohen_kappa_score(yte, pred)),
               "seconds": round(time.time() - t0, 1)}
        rows.append(row); fitted[name] = model
        print(f"{name:28s} CV {row['cv_acc_mean']:.4f}±{row['cv_acc_std']:.4f} | "
              f"test acc {row['test_acc']:.4f} | F1 {row['test_f1_macro']:.4f} | kappa {row['test_kappa']:.4f}")

    # model terbaik dipilih dari CV pada data latih (tidak mengintip data uji)
    best_name = max(rows, key=lambda r: (r["cv_acc_mean"], r["test_acc"]))["model"]
    best = fitted[best_name]
    pred = best.predict(Xte)
    print(f"\n>> Model terbaik: {best_name}")

    rep = classification_report(yte, pred, labels=labels, target_names=names, output_dict=True, zero_division=0)
    cm = confusion_matrix(yte, pred, labels=labels)

    # ---------- 4. grafik
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    cmn = cm / cm.sum(axis=1, keepdims=True).clip(min=1)
    im = ax.imshow(cmn, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(labels); ax.set_yticks(labels)
    ax.set_xticklabels(names, rotation=40, ha="right"); ax.set_yticklabels(names)
    for i in labels:
        for j in labels:
            ax.text(j, i, f"{cm[i, j]}\n({cmn[i, j]*100:.0f}%)", ha="center", va="center", fontsize=8,
                    color="white" if cmn[i, j] > 0.5 else "black")
    ax.set_xlabel("Prediksi"); ax.set_ylabel("Aktual"); ax.set_title(f"Confusion Matrix - {best_name}")
    fig.colorbar(im, fraction=0.046); fig.tight_layout()
    fig.savefig(C.RESULT_DIR / "confusion_matrix.png", dpi=140); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    order = sorted(rows, key=lambda r: r["test_acc"])
    ax.barh([r["model"] for r in order], [r["test_acc"] * 100 for r in order], color="#2e86c1")
    ax.set_xlabel("Akurasi data uji (%)"); ax.set_xlim(max(0, min(r["test_acc"] for r in rows) * 100 - 5), 100)
    for i, r in enumerate(order):
        ax.text(r["test_acc"] * 100 + 0.1, i, f"{r['test_acc']*100:.2f}", va="center", fontsize=8)
    ax.set_title("Perbandingan model"); fig.tight_layout()
    fig.savefig(C.RESULT_DIR / "perbandingan_model.png", dpi=140); plt.close(fig)

    pi = permutation_importance(best, Xte, yte, n_repeats=5, random_state=args.seed, scoring="accuracy", n_jobs=1)
    imp = sorted(zip(C.FEATURES, pi.importances_mean.tolist()), key=lambda t: t[1], reverse=True)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh([k for k, _ in imp][::-1], [v for _, v in imp][::-1], color="#27ae60")
    ax.set_xlabel("Penurunan akurasi (permutation importance)"); ax.set_title(f"Kepentingan fitur - {best_name}")
    fig.tight_layout(); fig.savefig(C.RESULT_DIR / "feature_importance.png", dpi=140); plt.close(fig)

    # ---------- 5. eksperimen jumlah data latih
    curve = []
    rng = np.random.RandomState(args.seed)
    for frac in [0.05, 0.1, 0.25, 0.5, 0.75, 1.0]:
        idx = np.concatenate([rng.choice(np.where(ytr == k)[0], max(5, int(frac * (ytr == k).sum())), replace=False)
                              for k in labels])
        m = clone(best).fit(Xtr[idx], ytr[idx])
        acc = float(accuracy_score(yte, m.predict(Xte)))
        curve.append({"fraksi": frac, "n_train": int(len(idx)), "test_acc": acc})
        print(f"  data latih {frac*100:5.1f}% ({len(idx)}) -> akurasi {acc:.4f}")
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([c["n_train"] for c in curve], [c["test_acc"] * 100 for c in curve], "o-")
    ax.set_xscale("log"); ax.set_xlabel("Jumlah data latih"); ax.set_ylabel("Akurasi uji (%)")
    ax.set_title("Eksperimen jumlah data"); ax.grid(alpha=.3); fig.tight_layout()
    fig.savefig(C.RESULT_DIR / "eksperimen_jumlah_data.png", dpi=140); plt.close(fig)

    # ---------- simpan
    joblib.dump({"model": best, "model_name": best_name, "features": C.FEATURES,
                 "class_ids": C.CLASS_IDS}, C.MODEL_FILE)
    results = {
        "n_raw_rows": int(n_raw), "n_clean_rows": int(sum(n_clean_counts.values())),
        "n_classes": len(labels), "class_names": names,
        "n_polygons": {C.CLASS_NAMES[k]: int(v) for k, v in
                       df.groupby("class_id")["poly_id"].nunique().items()},
        "clean_counts_per_class": n_clean_counts,
        "balanced": not args.no_balance,
        "n_train": int(len(train)), "n_test": int(len(test)),
        "train_per_class": counts(train), "test_per_class": counts(test),
        "test_frac_polygons": args.test_frac, "seed": args.seed,
        "features": C.FEATURES, "models": rows, "best_model": best_name,
        "best_test_acc": float(accuracy_score(yte, pred)),
        "best_test_f1_macro": float(f1_score(yte, pred, average="macro")),
        "best_test_kappa": float(cohen_kappa_score(yte, pred)),
        "classification_report": rep, "confusion_matrix": cm.tolist(),
        "feature_importance": imp, "data_size_experiment": curve,
    }
    json.dump(results, open(C.RESULTS_JSON, "w"), indent=2, ensure_ascii=False)
    print(f"\nTersimpan: {C.MODEL_FILE}, {C.RESULTS_JSON}, grafik di {C.RESULT_DIR}/")


if __name__ == "__main__":
    main()
