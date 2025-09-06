# AI Discoverability Scanner (GUI + Playwright)

Paste a URL, watch live status as your site is scanned (robots, headings, JSON-LD), and download a PDF report. Runs on Azure App Service (Linux, container).

## One‑Click: Deploy Azure Infrastructure
This button creates:
- App Service Plan (Linux)
- Web App (Linux)
- Storage Account
- Application Insights

> After infra is up, connect the Web App to **GitHub Deployment Center** to build/run the included Dockerfile.

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/REPLACE_WITH_RAW_URL_TO_INFRA/azuredeploy.json)

## Quick Deploy Steps
1. **Create a GitHub repo** and upload these files.
2. Replace `REPLACE_WITH_RAW_URL_TO_INFRA` above with your repo's raw URL (e.g., `https://raw.githubusercontent.com/<you>/<repo>/main/infra`), then click the button.
3. In Azure Portal → Resource Group, open your **Web App** → **Deployment Center**.
4. Choose **GitHub Actions**, select your repo/branch, and let Azure build/deploy the Dockerfile.
5. When deployment completes, browse: `https://<appName>.azurewebsites.net`

## App Settings (App Service → Configuration)
- `BRAND_NAME` = `AI Discoverability Scanner`
- `MAX_PAGES` = `10`
- `MAX_DEPTH` = `2`
- `PAGE_TIMEOUT_SEC` = `25`
- `WEBSITES_PORT` = `8000` (already set by template)

## Local Development (optional)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r app/requirements.txt
cd app && python app.py
# open http://localhost:8000
```

## Notes
- Playwright installs Chromium at container start (see `startup.sh`).
- For Entra ID sign-in later: enable **App Service Authentication** (no code changes needed).
- To store jobs/reports in Azure Blob, replace the simple local `Storage` class with Azure Blob SDK (using `AZURE_STORAGE_CONNECTION_STRING`).

---

### Project Structure
```
/ (root)
 ├─ app/
 │   ├─ app.py           # Flask app (GUI, routes, SSE status)
 │   ├─ scanner.py       # Playwright logic + parsing + scoring
 │   ├─ report.py        # PDF generator (ReportLab)
 │   ├─ storage.py       # Local storage (jobs/). Swap to Azure Blob later.
 │   ├─ templates/
 │   │   ├─ index.html
 │   │   └─ status.html
 │   ├─ static/
 │   │   └─ style.css
 │   ├─ requirements.txt
 │   └─ startup.sh
 ├─ Dockerfile
 └─ infra/
     └─ azuredeploy.json
```

## Troubleshooting
- **Playwright errors**: Ensure container is used (Deployment Center building Dockerfile).  
- **Report not downloading**: Wait for “Complete” status; the PDF builds at the end of the job.  
- **Timeouts**: Increase `PAGE_TIMEOUT_SEC` or reduce `MAX_PAGES`/`MAX_DEPTH` in App Settings.
