-- Fix migration dependency issue by marking professional_services.0001_initial as applied
-- This resolves: Migration main.0001_initial is applied before its dependency professional_services.0001_initial

INSERT INTO django_migrations (app, name, applied)
VALUES ('professional_services', '0001_initial', NOW())
ON CONFLICT (app, name) DO NOTHING;

-- Verify the migration is now recorded
SELECT app, name, applied FROM django_migrations 
WHERE app IN ('main', 'professional_services') 
ORDER BY applied;

