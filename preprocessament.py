
import pandas as pd

FITXER = "ds_24406_1.csv"
TRIMESTRE_INICI = "2023T1"   # comencem des de 2023 perquè Iryo va començar a operar a finals de 2022

# Transformem els noms d'emprese a noms mes curts per entedre millor
NOMS_EMPRESES = {
    "Renfe Viajeros": "Renfe",   # Renfe inclou tant AVE com Avlo
    "Iryo": "Iryo",
    "OUIGO": "Ouigo",
}
# com nomes ens interessa aquestes dades ficarem nombres mes curts per a les columnes
COLUMNES = {
    "Viajeros (Núm)": "Viatgers",
    "Plazas Ofertadas (Núm)": "Places",
}

"""
Llegeix el CSV original de la CNMC i el transforma en una tabla, DataFrame
"""
def carregar(fitxer: str = FITXER) -> pd.DataFrame:
   
    return pd.read_csv(fitxer, sep=";", encoding="utf-8-sig")



"""
    FILTRATGE:
        Aquesta funció només agafa les files que són d'alta velocitat (LD AV),
        de les tres empreses que ens interessen (Renfe, Iryo i Ouigo), del tipus de 
        corredor que no ens interessa ni Total ni Resto per això els eliminem, i com hem
        dit abans només agafem les dades a partir de 2023T1
"""
def filtrar(df: pd.DataFrame) -> pd.DataFrame:
    
    filtre = (
        (df["Tipo de producto"] == "LD AV")
        & (df["Empresa"].isin(NOMS_EMPRESES.keys()))
        & (~df["Corredor"].isin(["Total", "Resto"]))
        & (df["Trimestre"] >= TRIMESTRE_INICI)   
    )
    # filtre sera una llita on cada fila te un valor True o False depenent si compleix les condicions de dalt, i nomes agafarem les files que compleixen les condicions
    net = df.loc[filtre, ["Trimestre", "Corredor", "Empresa", *COLUMNES.keys()]]
    net = net.rename(columns=COLUMNES)              # cambaiem els noms de les columnes a noms mes curts per aixo hem fet el diccionari COLUMNES

    # Comprovació de que no hi ha valors buits a les columnes Viatgers i Places, si hi ha valors buits llavors llença un error amb el missatge "Hi ha valors buits"
    assert net[["Viatgers", "Places"]].notna().all().all(), "Hi ha valors buits"
    #return del DataFrame filtrat 
    return net.reset_index(drop=True)



"""
    AGRUPAMENT:
    Aquesta funcio agrupa les dades per trimestre i empresa, sumant els valors de viatgers i places
"""
def agrupar(df):
    return df.groupby(["Trimestre", "Empresa"], as_index=False)[["Viatgers", "Places"]].sum()


"""
    NORMALITZACIÓ:
    Aquesta funcio converteix els valors absoluts en mesures relatives.
    El nombre absolut de viatgers afavoreix Renfe, que opera molts més
    trens. Per comparar de forma justa es calcula, per a cada empresa i
    trimestre:
      - Quota de mercat (%) = viatgers de l'empresa / viatgers de les tres empreses en aquell trimestre x 100
      - Ocupació (%)        = viatgers de l'empresa / places ofertades x 100        
"""
def normalitzar(df: pd.DataFrame) -> pd.DataFrame:
    
    df = df.copy()
    # Calculem la quota de mercat i l'ocupació per a cada fila del DataFrame
    total_trimestre = df.groupby("Trimestre")["Viatgers"].transform("sum")
    df["Quota"] = df["Viatgers"] / total_trimestre * 100
    df["Ocupacio"] = df["Viatgers"] / df["Places"] * 100
    return df
 
 

"""
    RECONFIGURACIÓ I ORDENACIÓ:
    Modificacio del format de data a una data real, per a ordenar les dades, 
    també es crea una columna amb l'etiqueta llegible per la grafica final. 


"""
def reconfigurar(df: pd.DataFrame) -> pd.DataFrame:
    
    df = df.copy()
    # Cammbiem la T per Q ja que pandas es Q de quatyer en angles i la fncio to_timestamp() fa la conversio
    df["Data"] = pd.PeriodIndex(
        df["Trimestre"].str.replace("T", "Q"), freq="Q"
    ).to_timestamp()
    df["Etiqueta"] = "T" + df["Trimestre"].str[-1] + " " + df["Trimestre"].str[:4]

    # Cambiem els noms de les empreses a noms mes curts per a que es vegi millor a la grafica
    df["Empresa"] = df["Empresa"].map(NOMS_EMPRESES)
    # Ordenem les files per data i empresa, i resetejem l'index per a que sigui consecutiu
    return df.sort_values(["Data", "Empresa"]).reset_index(drop=True)
 
"""
 Aquesta funcio ordena les files del DataFrame segons la mesura que es passa com a parametre, de major a menor
"""
def ordenar(df: pd.DataFrame, mesura: str) -> pd.DataFrame:

    return df.sort_values(mesura, ascending=False)
 
"""
Aquesta funcio aplica tot el pipeline: filtrar -> agrupar -> normalitzar -> reconfigurar.
"""
def preparar(fitxer: str = FITXER) -> pd.DataFrame:
   
    net = filtrar(carregar(fitxer))
    return reconfigurar(normalitzar(agrupar(net)))

"""
Aquesta funcio desa les dades processades en un fitxer CSV amb separador de punts i coma, amb els valors de quota i ocupacio arrodonits a 2 decimals
"""
def desar(dades: pd.DataFrame, fitxer: str = "dades_processades.csv") -> None:
   
    sortida = dades.copy()
    sortida["Data"] = sortida["Data"].dt.strftime("%Y-%m-%d")
    sortida[["Viatgers", "Places"]] = sortida[["Viatgers", "Places"]].astype(int)
    sortida = sortida[["Data", "Etiqueta", "Empresa",
                       "Viatgers", "Places", "Quota", "Ocupacio"]]
    sortida.round({"Quota": 2, "Ocupacio": 2}).to_csv(
        fitxer, sep=";", decimal=",", index=False, encoding="utf-8-sig"
    )
    print(f"Dades desades a '{fitxer}' ({len(sortida)} files)")
 
if __name__ == "__main__":
    dades = preparar()
    desar(dades)
    