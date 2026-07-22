from __future__ import annotations

from collections import defaultdict


class InMemoryCourseRepository:
    def __init__(self):
        self.jobs = {}
        self.plans = {}
        self.courses = {}
        self.course_versions = {}
        self.job_versions = {}
        self._modules = {}
        self._lessons = {}
        self._objectives = defaultdict(list)
        self._blocks = defaultdict(list)
        self._citations = defaultdict(list)
        self.events = defaultdict(list)

    async def add_job(self, x):
        self.jobs[x.id] = x

    async def job_by_key(self, k):
        return next((x for x in self.jobs.values() if x.idempotency_key == k), None)

    async def get_job(self, i):
        return self.jobs.get(i)

    async def event(self, j, n, p):
        self.events[j.id].append({"stage": n, "payload": p})

    async def add_plan(self, x):
        self.plans[x.generation_job_id] = x

    async def add_course(self, x):
        self.courses[x.id] = x

    async def get_course(self, i):
        return self.courses.get(i)

    async def add_version(self, x, j):
        self.course_versions[x.id] = x
        self.job_versions[j] = x if j else self.job_versions.get(j)

    async def version_for_job(self, j):
        return self.job_versions.get(j)

    async def get_version(self, i):
        return self.course_versions.get(i)

    async def versions(self, c):
        return [x for x in self.course_versions.values() if x.course_id == c]

    async def add_module(self, x):
        self._modules[x.id] = x

    async def module_for(self, v, p):
        return next(
            (x for x in self._modules.values() if x.course_version_id == v and x.position == p),
            None,
        )

    async def modules(self, v):
        return sorted(
            (x for x in self._modules.values() if x.course_version_id == v),
            key=lambda x: x.position,
        )

    async def add_lesson(self, x):
        self._lessons[x.id] = x

    async def lesson_for(self, m, p):
        return next(
            (x for x in self._lessons.values() if x.module_id == m and x.position == p), None
        )

    async def lessons(self, m):
        return sorted(
            (x for x in self._lessons.values() if x.module_id == m), key=lambda x: x.position
        )

    async def add_objective(self, x, l):
        self._objectives[l].append(x)

    async def objectives(self, l):
        return self._objectives[l]

    async def add_block(self, x):
        self._blocks[x.lesson_id].append(x)

    async def blocks(self, l):
        return self._blocks[l]

    async def add_citation(self, x):
        if not any(
            c.claim_id == x.claim_id and c.content_block_id == x.content_block_id
            for c in self._citations[x.content_block_id]
        ):
            self._citations[x.content_block_id].append(x)

    async def citations(self, b):
        return self._citations[b]
