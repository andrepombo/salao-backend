# Auto Deploy to VPS (Backend)

This document explains how the **salao-backend** repo auto-deploys to your Hostinger VPS (`app2.andrepombo.info`) using GitHub Actions and Docker Compose.

The frontend repo has a similar document in its own `DEPLOYMENT.md`.

---

## 1. Architecture Overview

- **Git repo**: `salao-backend` on GitHub.
- **Branch that deploys**: `main`.
- **VPS**: Hostinger, domain `app2.andrepombo.info` behind Traefik.
- **Stack location on VPS**: `~/apps/app2/docker-compose.yml` with services:
  - `db`, `backend`, `frontend`.
- **Service name for backend**: `backend` in `docker-compose.yml`.

**Flow:**

1. You push to `main` in `salao-backend`.
2. GitHub Actions workflow `.github/workflows/deploy.yml` runs.
3. It syncs the backend code to the VPS at `~/apps/app2/backend`.
4. On the VPS, it runs `docker compose up -d --build backend` in `~/apps/app2`.
5. It performs a health check on `https://app2.andrepombo.info/api/` via Traefik.

---

## 2. One-Time VPS Setup

Run these steps once on your VPS.

### 2.1 Create / configure user `andre`

Most of this is already done, but for completeness:

```bash
# As root on the VPS
useradd -m -s /bin/bash andre || true

# As andre
su - andre
mkdir -p ~/apps/app2
```

Ensure your `docker-compose.yml` lives at `~/apps/app2/docker-compose.yml` and defines `backend` and `frontend` services.

### 2.2 Docker + Docker Compose plugin

On VPS, as root:

```bash
apt-get update
apt-get install -y docker-compose-plugin
```

Then as `andre`:

```bash
su - andre
docker compose version
```

You should see a version printed.

### 2.3 Allow `andre` to use Docker without sudo

```bash
# As root
usermod -aG docker andre
```

Log out and back in as `andre`, then verify:

```bash
ssh andre@app2.andrepombo.info
cd ~/apps/app2
docker ps
```

`docker ps` should work without `sudo`.

---

## 3. SSH Key for GitHub Actions (`VPS_SSH_KEY`)

GitHub Actions needs an SSH key to log into the VPS as `andre`.

On your local machine:

```bash
ssh-keygen -t ed25519 -C "github-actions-app2-backend"
# Example path: /home/lock221/.ssh/id_ed25519_app2
```

This creates:

- Private key: `~/.ssh/id_ed25519_app2`
- Public key: `~/.ssh/id_ed25519_app2.pub`

Add the public key to `andre` on the VPS:

```bash
ssh root@app2.andrepombo.info
su - andre

mkdir -p ~/.ssh
nano ~/.ssh/authorized_keys    # paste contents of id_ed25519_app2.pub
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

Test SSH from local:

```bash
ssh -i ~/.ssh/id_ed25519_app2 andre@app2.andrepombo.info
```

If it logs in without asking a password, you are ready to use this key in GitHub.

---

## 4. GitHub Secrets for Backend

In the **salao-backend** repository on GitHub:

1. Go to **Settings → Secrets and variables → Actions**.
2. Add/update these **secrets**:

### 4.1 VPS connection secrets

- `VPS_HOST` → `app2.andrepombo.info`
- `VPS_SSH_USER` → `andre`
- `VPS_SSH_KEY` → contents of your private key file `id_ed25519_app2`.

### 4.2 Backend application secrets

These are written into `.env` by the workflow:

- `ENV`
- `DEBUG`
- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
- `TIME_ZONE`
- `LANGUAGE_CODE`
- *(optional)* `DATABASE_URL` if you use it.

Example (not actual values):

```env
ENV=production
DEBUG=False
SECRET_KEY=your-super-secret-key
ALLOWED_HOSTS=app2.andrepombo.info
CORS_ALLOWED_ORIGINS=https://app2.andrepombo.info
TIME_ZONE=America/Sao_Paulo
LANGUAGE_CODE=pt-br
```

---

## 5. Backend Deploy Workflow Details

The workflow file is `.github/workflows/deploy.yml`.

Key parts:

- **Trigger**:

  ```yaml
  on:
    push:
      branches:
        - main
  ```

- **Checkout + .env creation**:

  ```yaml
  - uses: actions/checkout@v4

  - name: Create .env file
    env:
      ENV: ${{ secrets.ENV }}
      VPS_SSH_USER: ${{ secrets.VPS_SSH_USER }}
    run: |
      echo "ENV=${ENV}" >> .env
      echo "DEBUG=${{ secrets.DEBUG }}" >> .env
      echo "SECRET_KEY=${{ secrets.SECRET_KEY }}" >> .env
      echo "ALLOWED_HOSTS=${{ secrets.ALLOWED_HOSTS }}" >> .env
      echo "CORS_ALLOWED_ORIGINS=${{ secrets.CORS_ALLOWED_ORIGINS }}" >> .env
      echo "TIME_ZONE=${{ secrets.TIME_ZONE }}" >> .env
      echo "LANGUAGE_CODE=${{ secrets.LANGUAGE_CODE }}" >> .env
  ```

- **Sync backend code to VPS**:

  ```yaml
  - name: Copy files to VPS
    uses: easingthemes/ssh-deploy@main
    with:
      SSH_PRIVATE_KEY: ${{ secrets.VPS_SSH_KEY }}
      ARGS: "-rlgoDzvc -i"
      SOURCE: "./"
      REMOTE_HOST: ${{ secrets.VPS_HOST }}
      REMOTE_USER: ${{ secrets.VPS_SSH_USER }}
      TARGET: '/home/${{ secrets.VPS_SSH_USER }}/apps/app2/backend'
      EXCLUDE: "/dist/, /node_modules/, /.git/, /venv/, /__pycache__/, *.pyc"
  ```

- **Build & start backend container**:

  ```yaml
  - name: Build and start containers
    uses: appleboy/ssh-action@v0.1.10
    with:
      host: ${{ secrets.VPS_HOST }}
      username: ${{ secrets.VPS_SSH_USER }}
      key: ${{ secrets.VPS_SSH_KEY }}
      script: |
        cd /home/${{ secrets.VPS_SSH_USER }}/apps/app2
        echo "Building and starting backend container..."
        docker compose up -d --build backend
        echo "Waiting for services to start..."
        sleep 30
        echo "Checking container status for backend..."
        docker compose ps backend
  ```

- **Health check via Traefik**:

  ```yaml
  - name: Health check
    uses: appleboy/ssh-action@v0.1.10
    with:
      host: ${{ secrets.VPS_HOST }}
      username: ${{ secrets.VPS_SSH_USER }}
      key: ${{ secrets.VPS_SSH_KEY }}
      script: |
        echo "Performing backend health check via public API endpoint..."
        sleep 10

        if curl -f -s https://app2.andrepombo.info/api/ > /dev/null 2>&1; then
          echo "✅ API endpoint is responding"
        else
          echo "⚠️  API endpoint check failed"
          docker compose logs backend --tail=50
        fi

        echo "\nBackend container status:"
        docker compose ps backend

        echo "\nRecent backend logs:"
        docker compose logs backend --tail=20

        echo "\n🎉 Deployment health check completed!"
        echo "Your application should be accessible at: app2.andrepombo.info"
  ```

---

## 6. Day-to-Day Usage

To deploy backend changes:

1. Commit your code in `salao-backend`:

   ```bash
   git add .
   git commit -m "feat: something in backend"
   git push origin main
   ```

2. Go to the **Actions** tab in GitHub and open the latest **Deploy to VPS** run.
3. When the workflow is green, the backend is live behind Traefik at:

   - `https://app2.andrepombo.info/api/`

---

## 7. Related Docs

- Frontend deployment details live in the **salao-frontend** repo under `DEPLOYMENT.md`.
- Additional environment variable descriptions are in `README.md` under the Deploy section.
