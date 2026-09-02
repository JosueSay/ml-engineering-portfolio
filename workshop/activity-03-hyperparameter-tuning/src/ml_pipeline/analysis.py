"""Analisis y reporte de resultados del modelo (fase Evaluation de CRISP-DM)."""

import pandas as pd
from sklearn.model_selection import cross_val_score


def analizar_overfitting(metricas):
    """Analiza diferencia Train-Test y retorna diagnostico."""
    r2_diff = metricas['train']['r2'] - metricas['test']['r2']

    print("OVERFITTING ANALYSIS")
    print("-" * 60)
    print(f"Diferencia R_2 (Train - Test): {r2_diff:.4f}")

    if r2_diff < 0.05:
        status = "[OK] Modelo bien generalizado"
    elif r2_diff < 0.10:
        status = "[MODERADO] Overfitting moderado detectado"
    else:
        status = "[ALERTA] Overfitting significativo detectado"

    print(f"STATUS: {status}")
    return r2_diff


def mostrar_coeficientes(modelo):
    """Extrae y muestra coeficientes ordenados por magnitud."""
    feature_names = modelo.named_steps['preprocesamiento'].get_feature_names_out()
    coefficients = modelo.named_steps['modelo'].coef_
    intercept = modelo.named_steps['modelo'].intercept_

    coef_df = pd.DataFrame({
        'Feature': feature_names,
        'Coeficiente': coefficients
    }).sort_values('Coeficiente', key=abs, ascending=False)

    print("\nCOEFICIENTES DEL MODELO")
    print("-" * 60)
    print(f"Intercepto (beta_0): {intercept:.4f}")
    for idx, row in coef_df.iterrows():
        print(f"{row['Feature']:<30} {row['Coeficiente']:>10.4f}")

    return coef_df


def validacion_cruzada(modelo, X_train, y_train, cv=5):
    """Ejecuta validacion cruzada y reporta resultados."""
    cv_scores = cross_val_score(modelo, X_train, y_train, cv=cv, scoring='r2')

    print(f"\nVALIDACION CRUZADA ({cv} folds)")
    print("-" * 60)
    print(f"R_2 scores: {[f'{s:.4f}' for s in cv_scores]}")
    print(f"Media: {cv_scores.mean():.4f}")
    print(f"Desv.Est: {cv_scores.std():.4f}")

    return cv_scores
