# src/mi_pipeline/core.py
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split

def obtener_datos(file_id='10S8JVFiLfCoRB9mb0NJG5YhITyXbH37B'):
    download_url = f'https://drive.google.com/uc?export=download&id={file_id}'
    data = pd.read_csv(download_url)
    return data

def filtrar_datos(data):
    return data.drop(columns=["Sl_No", "Customer Key"])

def separar_datos(X):
    # Primero separamos el 20% para test
    X_train_val, X_test = train_test_split(X, test_size=0.20, random_state=42)
    # Luego el 25% del 80% restante para validación (que equivale al 20% del total)
    X_train, X_val = train_test_split(X_train_val, test_size=0.25, random_state=42)
    return X_train, X_val, X_test

def crear_pipeline():
    pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("pca", PCA(n_components=0.95))
    ])
    return pipeline
