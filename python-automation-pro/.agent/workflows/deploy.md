---
description: Steps to deploy the application to a production server
---
# Deployment Workflow

// turbo-all

1. Ensure all changes are committed and pushed to your git repository.
2. SSH into your production server.
3. Pull the latest changes: `git pull origin main`
4. Install dependencies: `composer install --no-dev --optimize-autoloader`
5. Run migrations: `php artisan migrate --force`
6. Compile assets: `npm install && npm run build`
7. Optimize:
    - `php artisan config:cache`
    - `php artisan route:cache`
    - `php artisan view:cache`
8. Restart Queue Worker: `php artisan queue:restart`
9. Verification: `php artisan test`
