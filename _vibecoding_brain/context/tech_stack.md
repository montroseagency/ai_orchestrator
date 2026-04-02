# Montrroase Tech Stack Reference
> For Planner and Implementer agents. Architectural decisions and stack specifics.

## Frontend (Next.js 15 / React 19)

### Core Dependencies
- **next** ^15.5.12 — App Router, Server Components
- **react** 19.2.0 / **react-dom** 19.2.0
- **tailwindcss** ^4 — utility-first CSS (v4, with `@theme` syntax in globals.css)
- **framer-motion** ^11 — animations
- **@tanstack/react-query** ^5 — server state management
- **@phosphor-icons/react** — icon library (legacy: lucide-react exists but all new code MUST use Phosphor)
- **@dnd-kit/core** + sortable — drag and drop
- **socket.io-client** ^4.8 — real-time messaging/notifications
- **recharts** ^2 — charts/analytics
- **sonner** ^1.7 — toast notifications
- **date-fns** ^4 — date formatting/manipulation
- **clsx** + **tailwind-merge** — conditional class merging
- **react-markdown** + **rehype-sanitize** — markdown rendering

### Routing
- Next.js App Router. All pages in `client/app/`
- Protected routes handled in `client/middleware.ts`
- Auth: JWT stored in cookies, managed by `client/lib/auth-context.tsx`

### Data Fetching Pattern
```typescript
// ALWAYS use the typed API client:
import { functionName } from '@/lib/api'
// Or for module-specific:
import { specificFn } from '@/lib/api/module'

// React Query pattern:
const { data, isLoading, error } = useQuery({
  queryKey: ['resource', id],
  queryFn: () => fetchResource(id),
})

// Mutations:
const mutation = useMutation({
  mutationFn: updateResource,
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ['resource'] }),
})
```

### File Conventions
```
app/[route]/page.tsx         ← Page (Server Component by default)
app/[route]/layout.tsx       ← Layout wrapper
components/[area]/ComponentName.tsx   ← Component files
components/ui/               ← Primitive shared UI components
lib/hooks/                   ← Custom React hooks
lib/types/                   ← TypeScript type definitions
lib/api/                     ← Modular API client functions
```

### TypeScript
- Strict mode on. Type everything.
- No `any` unless unavoidable — use `unknown` + type guards instead.
- Types shared via `client/lib/types.ts` and `client/lib/websiteTypes.ts`

### Testing
- **Vitest** + **@testing-library/react**
- Config: `client/vitest.config.ts`
- Run: `npm test` in `client/`

---

## Backend (Django 4 / DRF)

### Core Dependencies (server/requirements.txt)
- **Django** + **djangorestframework** — core
- **django-cors-headers** — CORS
- **djangorestframework-simplejwt** — JWT auth
- **channels** + **daphne** — WebSockets
- **celery** + **django-celery-beat** — async tasks / scheduling
- **psycopg2** — PostgreSQL
- **Pillow** — image processing
- **boto3** — S3/cloud storage

### API Structure
```
server/api/
├── models/          ← Django ORM models (one file per domain)
├── views/           ← DRF viewsets (one file per domain)
├── serializers/     ← DRF serializers (one file per domain)
├── tasks/           ← Celery async tasks
├── utils/           ← Shared helpers
├── urls.py          ← ALL URL registrations (Router + path())
└── services/        ← Business logic services
```

### URL Registration Pattern
```python
# In server/api/urls.py
router = DefaultRouter()
router.register(r'resource', ResourceViewSet, basename='resource')

# Manual paths (non-viewset):
path('custom-endpoint/', CustomView.as_view(), name='custom'),
```

### ViewSet Pattern
```python
class ResourceViewSet(viewsets.ModelViewSet):
    serializer_class = ResourceSerializer
    permission_classes = [IsAuthenticated]
    queryset = Resource.objects.all()

    def get_queryset(self):
        # Always scope to current user/role
        return super().get_queryset().filter(user=self.request.user)
```

### Auth & Permissions
```python
from rest_framework.permissions import IsAuthenticated
from api.permissions import IsAgent, IsAdmin, IsClient  # custom
```

### Key Models (domain overview)
- **User model:** Extended Django user with roles (admin/agent/client)
- **Client:** Marketing client records, linked to agents
- **Task:** Unified task management with Kanban support
- **Schedule:** Agent scheduling with DaySchedule model
- **MarketingPlan:** Campaign planning and approval workflow
- **Message/Room:** Real-time messaging via WebSockets

---

## Infrastructure
- **PostgreSQL** — primary DB
- **Redis** — cache + Celery broker + WebSocket channel layer
- **RabbitMQ** — alternative message broker (see docker-compose)
- **Nginx** — reverse proxy
- **Docker Compose** — local dev + production
- **Celery** — background tasks (emails, notifications, scheduling)

## Development Commands
```bash
# Frontend
cd client && npm run dev          # Start Next.js dev server (port 3000)
cd client && npm test             # Run Vitest tests

# Backend
cd server && python manage.py runserver   # Dev server (port 8000)
cd server && python manage.py makemigrations && python manage.py migrate
cd server && python manage.py test        # Run Django tests

# Docker
docker-compose -f docker-compose.dev.yml up   # Full dev stack
```

## NEVER DO
1. Never call `fetch()` directly — use `lib/api.ts`
2. Never skip authentication on API endpoints
3. Never put business logic in serializers — use `services/`
4. Never import server-only modules in client components
5. Never use `!important` in CSS unless overriding Tailwind v4 specificity
6. Never create a new DB model without a migration
7. Never commit `.env` files — use `.env.example` patterns
8. Never bypass React Query cache — always invalidate on mutation success
