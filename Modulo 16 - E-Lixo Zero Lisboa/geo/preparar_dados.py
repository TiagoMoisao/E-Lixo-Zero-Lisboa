# Instalar estas bibliotecas no terminal: pip install geopandas pandas
import geopandas as gpd

#Ler o ficheiro Shapefile principal
caminho_shp = "geo/d306_ponto_recolha_eletronicos_pub_vw.shp"
dados = gpd.read_file(caminho_shp)

# Filtrar os dados onde a coluna 'localidade' (ou 'concelho') é Lisboa
# Convertendo para minúsculas para evitar erros de formatação como 'LISBOA' ou 'Lisboa'
dados_lisboa = dados[dados['localidade'].str.lower() == 'lisboa']

# Guardar os dados filtrados num ficheiro CSV (muito mais leve e fácil de ler)
dados_lisboa.to_csv('pontos_lisboa.csv', index=False)

print("Dados de Lisboa extraídos com sucesso!")