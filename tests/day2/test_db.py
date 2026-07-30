import pytest
from app.repositories.task import TaskRepository


class TestRepositoryCreate:
    async def test_create_task(self, repo: TaskRepository):
        task = await repo.create(title="Test task")
        assert task.id >= 1
        assert task.title == "Test task"
        assert task.completed is False

    async def test_create_task_full(self, repo: TaskRepository):
        task = await repo.create(title="Full", description="Desc", completed=True)
        assert task.title == "Full"
        assert task.description == "Desc"
        assert task.completed is True


class TestRepositoryGet:
    async def test_get_existing(self, repo: TaskRepository):
        created = await repo.create(title="Find")
        found = await repo.get(created.id)
        assert found is not None
        assert found.title == "Find"

    async def test_get_missing(self, repo: TaskRepository):
        found = await repo.get(999)
        assert found is None


class TestRepositoryList:
    async def test_list_empty(self, repo: TaskRepository):
        tasks = await repo.list()
        assert tasks == []

    async def test_list_multiple(self, repo: TaskRepository):
        await repo.create(title="A")
        await repo.create(title="B")
        tasks = await repo.list()
        assert len(tasks) == 2


class TestRepositoryUpdate:
    async def test_update_existing(self, repo: TaskRepository):
        created = await repo.create(title="Old")
        updated = await repo.update(created.id, title="New", completed=True)
        assert updated is not None
        assert updated.title == "New"
        assert updated.completed is True

    async def test_update_missing(self, repo: TaskRepository):
        updated = await repo.update(999, title="Nope")
        assert updated is None


class TestRepositoryDelete:
    async def test_delete_existing(self, repo: TaskRepository):
        created = await repo.create(title="Del")
        deleted = await repo.delete(created.id)
        assert deleted is True

        found = await repo.get(created.id)
        assert found is None

    async def test_delete_missing(self, repo: TaskRepository):
        deleted = await repo.delete(999)
        assert deleted is False


class TestRepositoryPaginate:
    async def test_paginate_empty(self, repo: TaskRepository):
        page = await repo.paginate(page=1, per_page=10)
        assert page.total == 0
        assert page.items == []
        assert page.pages == 1

    async def test_paginate_with_data(self, repo: TaskRepository):
        for i in range(5):
            await repo.create(title=f"Task {i}")

        page1 = await repo.paginate(page=1, per_page=2)
        assert page1.total == 5
        assert len(page1.items) == 2
        assert page1.pages == 3
        assert page1.page == 1

        page3 = await repo.paginate(page=3, per_page=2)
        assert len(page3.items) == 1
