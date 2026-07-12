# TODO

Remaining work, in priority order.

## 1. Deploy to Cloud Run and verify the public URL
IAM role granted, key rotated — ready to deploy from the repo root:
```
gcloud run deploy haircut-ai --source . --region asia-southeast1 --memory 1Gi --allow-unauthenticated --set-env-vars OPENAI_API_KEY=<key>
```
Verify the printed `*.run.app` URL loads and a text-only recommendation works end to end.

## 2. Add live demo URL and screenshot to README
Once deployed, put the public URL prominently at the top of `README.md` plus a screenshot
(or GIF) of the app. Highest-value portfolio polish.

## 3. Swap feedback storage from CSV to Firestore
`feedback.csv` is ephemeral on Cloud Run (lost when the instance recycles). Write feedback
to Firestore when GCP credentials are available, keeping CSV as the local fallback.
Requires enabling Firestore in the `haircutrag` project. (Approach pending confirmation —
Firestore proposed over Sheets/BigQuery.)

## 4. Commit and push pending changes
Feedback feature with dissatisfied-user suggestions (`services/feedback.py`, UI changes,
tests), Docker files (`Dockerfile`, `.dockerignore`, `.gcloudignore`), README updates,
`.gitignore`, this file.
