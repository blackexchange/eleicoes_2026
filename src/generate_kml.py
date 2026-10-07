import sys
from pathlib import Path
import duckdb

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def generate_kml():
    duckdb_path = "data/processed/eleicoes.duckdb"
    con = duckdb.connect(duckdb_path)

    records = con.execute("""
        SELECT 
            NM_MUNICIPIO, ZONA, SECAO, NUMERO_URNA, LOCAL_VOTACAO, 
            ENDERECO, BAIRRO, LATITUDE, LONGITUDE, TOTAL_ELEITORES, DATA_CARGA
        FROM urnas_anteriores_UE2020_BA_geo
        WHERE LATITUDE IS NOT NULL AND LONGITUDE IS NOT NULL
        ORDER BY NM_MUNICIPIO, ZONA, SECAO
    """).fetchall()

    kml_path = Path("data/processed/urnas_anteriores_UE2020_Bahia_2026.kml")

    with open(kml_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
        f.write('  <Document>\n')
        f.write('    <name>Urnas Anteriores a UE2020 (UE2015) - Bahia 2026</name>\n')
        f.write('    <description>Mapeamento de 7.989 urnas de modelo anterior a UE2020 na Bahia</description>\n')

        for r in records:
            mun, zona, sec, n_urna, loc_vot, endr, bairro, lat, lon, eleitores, dt_carga = r
            desc = (
                f"<b>Município:</b> {mun}<br/>"
                f"<b>Zona:</b> {zona} | <b>Seção:</b> {sec}<br/>"
                f"<b>Número da Urna:</b> {n_urna} (Modelo UE2015)<br/>"
                f"<b>Local de Votação:</b> {loc_vot}<br/>"
                f"<b>Endereço:</b> {endr} - {bairro}<br/>"
                f"<b>Total de Eleitores:</b> {eleitores}<br/>"
                f"<b>Data/Hora Carga:</b> {dt_carga}"
            )
            f.write("    <Placemark>\n")
            f.write(f"      <name>{mun} - Z{zona:03d} S{sec:04d} (Urna {n_urna})</name>\n")
            f.write(f"      <description><![CDATA[{desc}]]></description>\n")
            f.write("      <Point>\n")
            f.write(f"        <coordinates>{lon},{lat},0</coordinates>\n")
            f.write("      </Point>\n")
            f.write("    </Placemark>\n")

        f.write("  </Document>\n")
        f.write("</kml>\n")

    print(f"✅ KML gerado com sucesso em: {kml_path} ({len(records):,} pontos)")
    con.close()


if __name__ == "__main__":
    generate_kml()
