# Figura 15 — Expansão hipotética da cobertura 5G em Goiânia

A figura apresenta uma **otimização espacial de máxima cobertura** com três estações radiobase (ERBs) hipotéticas. O painel (a) maximiza o número de moradores adicionais alcançados. O painel (b) maximiza a área adicional em setores censitários rurais. As estrelas identificam os locais escolhidos em cada painel.

## Alcance adotado para 3,5 GHz

A figura revisada usa **1 km como raio de referência** e a análise de sensibilidade avalia **0,5 km e 1,5 km**. Esses valores são hipóteses exploratórias. A frequência, por si só, não determina o alcance. Relevo, obstruções, altura e ganho das antenas, potência, interferência e as condições de visada afetam o orçamento do enlace. O raio de **4 km** foi mantido apenas como referência histórica para conferir a reprodução dos resultados anteriores. Seu uso como hipótese de cobertura operacional em 3,5 GHz exigiria justificativa específica e validação de campo.

Para agricultura de precisão, a métrica de cobertura deve refletir a aplicação. Para envio de imagens de drones, por exemplo, uma etapa posterior deve definir a taxa mínima de uplink, considerar a altura de operação e verificar a disponibilidade do enlace com um modelo de propagação adequado e medições de campo. Os hectares estimados neste exercício correspondem a setores censitários rurais, que incluem diversos usos do solo.

## Dados e cálculo

- **IBGE.** Malha com atributos dos setores censitários do Censo 2022, filtrada para Goiânia (código 5208707). A população foi distribuída uniformemente dentro de cada setor e atribuída a pontos em uma grade de 100 m. Cada ponto rural representa 1 ha.
- **Anatel.** A cobertura de referência foi reconstruída aproximadamente a partir dos pixels do raster fornecido na rodada original. A linha tracejada mostra o contorno aproximado. O cruzamento espacial utiliza SIRGAS 2000 / UTM zona 22S (EPSG:31982).
- **Busca exaustiva.** Foram avaliados os 5.456 trios possíveis entre os mesmos 33 locais candidatos da análise original. Um ponto contribui para o ganho se estiver fora da cobertura de referência e dentro do raio de pelo menos uma das três estações. Cada ponto conta uma vez. Empates no objetivo principal são resolvidos pelo maior ganho no outro objetivo.
- **Visualização.** As camadas de população e área rural são agregadas em células de 1 km. O ganho de cobertura é mostrado na resolução de cálculo de 100 m.

## Resultados

Os valores de população abaixo foram arredondados ao morador mais próximo. O CSV contém os valores calculados e as coordenadas dos locais selecionados.

| Raio por ERB | Critério de seleção | Moradores adicionais | Hectares adicionais em setores rurais |
|---|---|---:|---:|
| 0,5 km | Ambos selecionam o mesmo trio | 23 | 240 |
| 1,0 km | População | 70 | 747 |
| 1,0 km | Área rural | 56 | 910 |
| 1,5 km | População | 120 | 1.523 |
| 1,5 km | Área rural | 105 | 1.770 |
| 4,0 km (referência histórica) | Ambos selecionam o mesmo trio | 200 | 3.111 |

A escolha do raio altera os resultados. Com 1 km e 1,5 km, os objetivos selecionam trios diferentes. Com 0,5 km, os dois critérios selecionam o mesmo trio dentro da grade de locais candidatos utilizada. Como os centros candidatos estão espaçados em 1 km, o cenário de 0,5 km também deve ser interpretado à luz dessa resolução espacial.

## Reprodução

Use Python com os módulos `numpy`, `matplotlib`, `Pillow` e os bindings Python do GDAL (`osgeo`). Baixe `GO_setores_CD2022.zip` no diretório oficial do IBGE e use a imagem original `Goiania_Anatel_Agricultura.png` como segundo argumento. O alinhamento por pixels do script é específico dessa imagem de entrada.

```sh
python figura15.py GO_setores_CD2022.zip Goiania_Anatel_Agricultura.png
```

O script grava `Figura15_Goiania_1km.png` (300 dpi) e `sensibilidade_figura15.csv` no diretório de execução. A rodada de 4 km reproduz o resultado anterior de aproximadamente 200 moradores e 3.111 ha em setores rurais.

## Fontes

- [IBGE — Malha de setores censitários com atributos, Goiás](https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/malha_com_atributos/setores/shp/UF/GO/)
- [Imagem de entrada da análise anterior](https://chatgpt.com/library?file_id=libfile_7c3e4da1dd34819194ced4c021b094fc&account_id=personal)
- [Anatel — Cobertura da telefonia móvel](https://www.gov.br/anatel/pt-br/dados/qualidade/qualidade-dos-servicos/cobertura-da-telefonia-movel)
- [3GPP TR 38.901 — Modelos de canal](https://portal.3gpp.org/desktopmodules/Specifications/SpecificationDetails.aspx?specificationId=3173)
- [Halvarsson et al. (2018) — 5G NR Testbed 3.5 GHz Coverage Results](https://doi.org/10.1109/VTCSpring.2018.8417704)
- [Church e ReVelle (1974) — The Maximal Covering Location Problem](https://doi.org/10.1111/j.1435-5597.1974.tb00902.x)
