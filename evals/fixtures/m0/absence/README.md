# M0 fixture — removed authorization guard

**AC:** "The admin user listing remains restricted to admins."

Before: `/admin/users` is decorated with `@require_admin`.
After: the import and the decorator are gone; the route is unchanged.

A correct pass must:

- report an **absence** finding at the deleted decorator or the route;
- not treat the absence as a pass because the new file has no line for it;
- return `BLOCK` (P0).
