# Person 1 presentation notes

Slides: 1 title/team; 2 problem/intended users; 3 solution/core features;
5 architecture/data flow. Current implementation is the public foundation only.

TravelMate helps travelers organize trips, destinations, dates, budgets, and
activities. Users see personal information; admins have separately protected
system access. Explain only completed behavior as working in the final demo.

Trace a completed Create Trip flow: form → Person 2's fetch with JSON → Person
3's POST route → Person 4's verified session identity → input/ownership checks
→ MongoDB insert → JSON → dashboard rendering. Refresh proves persistence.

Show exact files/functions after integration, explain how PRs and post-merge
checks protect the shared application, and explain why the browser never
receives database credentials or talks directly to MongoDB.

Demo order: homepage, user login, create/read/refresh/edit, activities if included,
delete, logout, admin login/list, normal-user admin denial, architecture recap.
Person 3 explains CRUD routes; Person 4 explains auth/database; Person 2 explains
UI/fetch; Person 5 explains admin/activities/test evidence. Rehearse without
handing off questions about your own responsibilities.
