# Deployment handoff

The original setup instructions are superseded by README.md and the GitHub
Actions workflow. Use today's America/Boise date for deployment, never a fixed
test date. Generate into ignored _site/, never commit Scripture text. Keep
ESV_API_KEY in repository Actions secrets. Validate all readings with the
source fixture and documented errata in validation/README.md. The legacy
setup-and-deploy.ps1 is not needed for deployment.
