# Docker Credential Policy

FoodInsightAI should not require credentials in a Dockerfile.

Use environment injection:

```cmd
docker compose --env-file .env -f docker/docker-compose.training.yml up --build
```

The only expected optional model credential is:

```text
HF_TOKEN
```

A public Hugging Face model does not require it.

Database/API credentials used by the broader FoodInsightAI application are intentionally not reproduced in this training bundle because they belong to the deployment environment, not the model-training code.

Never commit `.env`.
