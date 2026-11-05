# Mini DataLab

Aplicacao local para explorar arquivos CSV, identificar problemas de qualidade e
gerar interpretacoes automaticas para graficos.

## Recursos

- Metadados, tipos de coluna e uso de memoria.
- Contagem de valores ausentes e linhas duplicadas, com alertas.
- Estatisticas descritivas e correlacoes numericas fortes.
- Conclusoes consolidadas sobre a qualidade e o perfil dos dados.
- Graficos de frequencia (barras e pizza), histogramas e dispersoes numericas,
  acompanhados de interpretacao textual.

## Executar no Windows

No terminal, dentro desta pasta:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

O Streamlit abrira o aplicativo no navegador. Envie um CSV na barra lateral ou
selecione a base de exemplo.

## Usar a analise em Python

```python
import pandas as pd
from analytics import analyze_dataframe, interpret_chart

data = pd.read_csv("dados.csv")
results = analyze_dataframe(data)
print(results["conclusions"])
print(interpret_chart("histograma", data, x="idade"))
```
