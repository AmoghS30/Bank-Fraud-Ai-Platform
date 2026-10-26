Score a transaction through the LightGBM risk model and return the risk score with a SHAP explanation.

## Usage
/risk-score <transaction JSON or account_id + amount + description>

## Steps
1. If $ARGUMENTS is a raw JSON object, use it directly as the transaction. If it's a description (e.g. "account A123 sending 50000 at 3am to new recipient"), convert it to the expected feature schema first by checking `risk_model/feature_schema.json`.
2. Confirm the model file exists: `ls risk_model/model.pkl` (or `model.cbm` / `model.txt` depending on what was saved in Stage 2). If it doesn't exist yet, tell the user Stage 2 needs to be completed first.
3. Run the scoring script:
```bash
python3 risk_model/score.py --transaction '$ARGUMENTS'
```
4. If `score.py` doesn't exist yet, run inference inline:
```bash
python3 -c "
import joblib, json, shap, numpy as np
model = joblib.load('risk_model/model.pkl')
tx = json.loads('$ARGUMENTS')
features = np.array([[tx[k] for k in model.feature_names_in_]])
score = model.predict_proba(features)[0][1]
explainer = shap.TreeExplainer(model)
shap_vals = explainer.shap_values(features)[1][0]
top = sorted(zip(model.feature_names_in_, shap_vals), key=lambda x: abs(x[1]), reverse=True)[:5]
print(f'Risk score: {score:.3f}')
print('Top drivers:', top)
"
```
5. Present output as:
   - **Risk score**: 0.0–1.0 with a label (Low < 0.4, Medium 0.4–0.7, High > 0.7, Critical > 0.9)
   - **Top 5 SHAP drivers**: feature name + direction (pushed score up/down) + magnitude

## Notes
- Prerequisites: Stage 2 complete, `risk_model/model.pkl` exists, `.venv` active.
- If score is above 0.7, automatically suggest running `/graph-explain` on the account to check network-level risk.
