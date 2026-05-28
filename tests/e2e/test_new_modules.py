"""
E2E Test Suite: New Modules
Tests for Users, Profile, Portfolio, Admin Dashboard
Covers: CRUD, role-based access, integration flows
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import time


def _unwrap(response_data, *keys):
    """Navigate nested response envelope: data -> key -> ... """
    val = response_data
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k, val)
    return val


# ============================================================================
# ADMIN USERS MODULE  /api/users
# ============================================================================

@pytest.mark.admin
class TestAdminUsers:
    """Admin user management via /api/users"""

    def test_admin_can_list_users(self, client: TestClient, admin_headers):
        response = client.get("/api/users", headers=admin_headers)
        assert response.status_code == 200, f"{response.status_code}: {response.text}"
        data = response.json()
        # Response: {"success": True, "data": {"users": [...]}}
        users = _unwrap(data, "data", "users")
        assert isinstance(users, list)
        print(f"\n✅ Admin list users: {len(users)} users")

    def test_admin_can_get_current_user(self, client: TestClient, admin_headers):
        response = client.get("/api/users/me", headers=admin_headers)
        assert response.status_code == 200, f"{response.status_code}: {response.text}"
        data = response.json()
        # Response: {"success": True, "data": {"user": {...}}}
        user = _unwrap(data, "data", "user")
        assert "email" in user
        assert user["role"] == "admin"
        print(f"\n✅ Admin GET /users/me: {user['email']}")

    def test_admin_can_create_user(self, client: TestClient, admin_headers):
        unique = int(time.time() * 1000)
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "email": f"newuser{unique}@example.com",
                "password": "NewUser@2026",
                "name": "New User Test",
                "role": "client"
            }
        )
        assert response.status_code in [200, 201], f"Got {response.status_code}: {response.text}"
        data = response.json()
        user = _unwrap(data, "data", "user")
        assert isinstance(user, dict)
        print(f"\n✅ Admin created user")

    def test_admin_can_update_user(self, client: TestClient, admin_headers):
        unique = int(time.time() * 1000)
        create = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "email": f"updateme{unique}@example.com",
                "password": "Update@2026",
                "name": "To Update",
                "role": "client"
            }
        )
        assert create.status_code in [200, 201]
        created = create.json()
        user = _unwrap(created, "data", "user")
        user_id = user.get("id") or user.get("_id")
        if not user_id:
            pytest.skip("Could not extract user ID from create response")

        resp = client.put(
            f"/api/users/{user_id}",
            headers=admin_headers,
            json={"name": "Updated Name"}
        )
        assert resp.status_code in [200, 201], f"{resp.status_code}: {resp.text}"
        print(f"\n✅ Admin updated user {user_id}")

    def test_admin_can_delete_user(self, client: TestClient, admin_headers):
        unique = int(time.time() * 1000)
        create = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "email": f"deleteme{unique}@example.com",
                "password": "Delete@2026",
                "name": "To Delete",
                "role": "client"
            }
        )
        assert create.status_code in [200, 201]
        created = create.json()
        user = _unwrap(created, "data", "user")
        user_id = user.get("id") or user.get("_id")
        if not user_id:
            pytest.skip("Could not extract user ID")

        resp = client.delete(f"/api/users/{user_id}", headers=admin_headers)
        assert resp.status_code in [200, 204], f"{resp.status_code}: {resp.text}"
        print(f"\n✅ Admin deleted user {user_id}")

    def test_client_cannot_list_users(self, client: TestClient, client_headers):
        response = client.get("/api/users", headers=client_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print(f"\n✅ Access control: client blocked from /api/users")

    def test_barber_cannot_list_users(self, client: TestClient, barber_headers):
        response = client.get("/api/users", headers=barber_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print(f"\n✅ Access control: barber blocked from /api/users")

    def test_unauthenticated_cannot_list_users(self, client: TestClient):
        response = client.get("/api/users")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"\n✅ Access control: unauthenticated blocked from /api/users")


# ============================================================================
# ADMIN DASHBOARD  /api/admin/dashboard
# ============================================================================

@pytest.mark.admin
class TestAdminDashboard:
    """Admin dashboard stats and alerts"""

    def test_admin_can_get_stats(self, client: TestClient, admin_headers):
        response = client.get("/api/admin/dashboard/stats", headers=admin_headers)
        assert response.status_code == 200, f"{response.status_code}: {response.text}"
        body = response.json()
        # Response: {"success": True, "data": {...stats...}}
        data = _unwrap(body, "data") if "data" in body else body
        expected_keys = ["total_clients", "total_barbers", "today_appointments"]
        for key in expected_keys:
            assert key in data, f"Missing key: {key} in {list(data.keys())}"
        print(f"\n✅ Admin dashboard stats OK")

    def test_admin_can_get_alerts(self, client: TestClient, admin_headers):
        response = client.get("/api/admin/dashboard/alerts", headers=admin_headers)
        assert response.status_code == 200, f"{response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, dict)
        print(f"\n✅ Admin dashboard alerts OK")

    def test_client_cannot_access_admin_stats(self, client: TestClient, client_headers):
        response = client.get("/api/admin/dashboard/stats", headers=client_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print(f"\n✅ Access control: client blocked from admin stats")

    def test_barber_cannot_access_admin_stats(self, client: TestClient, barber_headers):
        response = client.get("/api/admin/dashboard/stats", headers=barber_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print(f"\n✅ Access control: barber blocked from admin stats")

    def test_stats_numeric_values(self, client: TestClient, admin_headers):
        response = client.get("/api/admin/dashboard/stats", headers=admin_headers)
        assert response.status_code == 200
        body = response.json()
        data = _unwrap(body, "data") if "data" in body else body
        numeric_keys = ["total_clients", "total_barbers", "today_appointments"]
        for key in numeric_keys:
            if key in data:
                assert isinstance(data[key], (int, float)), \
                    f"{key} should be numeric, got {type(data[key])}"
        print(f"\n✅ Dashboard stats have correct numeric types")


# ============================================================================
# PROFILE MODULE  /api/profile
# ============================================================================

@pytest.mark.client
class TestClientProfile:
    """Client profile GET/PUT/password"""

    def test_client_can_get_profile(self, client: TestClient, client_headers):
        response = client.get("/api/profile", headers=client_headers)
        assert response.status_code == 200, f"{response.status_code}: {response.text}"
        body = response.json()
        # Response: {"success": True, "data": {...user fields...}}
        data = _unwrap(body, "data") if "data" in body else body
        assert "email" in data or "role" in data
        print(f"\n✅ Client GET /profile")

    def test_client_can_update_profile(self, client: TestClient, client_headers):
        response = client.put(
            "/api/profile",
            headers=client_headers,
            json={"name": "Updated Client Name", "phone": "555-1234"}
        )
        assert response.status_code in [200, 201], f"{response.status_code}: {response.text}"
        print(f"\n✅ Client PUT /profile")

    def test_client_can_change_password(self, client: TestClient):
        unique = int(time.time() * 1000)
        reg = client.post(
            "/api/auth/register",
            json={
                "email": f"pwchange{unique}@example.com",
                "password": "OldPass@2026",
                "name": "Password Change Test",
                "role": "client"
            }
        )
        assert reg.status_code in [200, 201], f"Register failed: {reg.text}"
        reg_data = reg.json()
        token = reg_data.get("token") or reg_data.get("access_token")
        assert token, f"No token in: {reg_data}"
        headers = {"Authorization": f"Bearer {token}"}

        response = client.put(
            "/api/profile/password",
            headers=headers,
            json={"current_password": "OldPass@2026", "new_password": "NewPass@2026"}
        )
        assert response.status_code in [200, 201], f"{response.status_code}: {response.text}"
        print(f"\n✅ Client changed password")

    def test_wrong_current_password_rejected(self, client: TestClient, client_headers):
        response = client.put(
            "/api/profile/password",
            headers=client_headers,
            json={"current_password": "WrongPass@9999", "new_password": "NewPass@2026"}
        )
        assert response.status_code in [400, 401, 422], \
            f"Expected 400/401/422, got {response.status_code}: {response.text}"
        print(f"\n✅ Wrong password correctly rejected: {response.status_code}")


@pytest.mark.barber
class TestBarberProfile:
    """Barber profile management"""

    def test_barber_can_get_profile(self, client: TestClient, barber_headers):
        response = client.get("/api/profile", headers=barber_headers)
        assert response.status_code == 200, f"{response.status_code}: {response.text}"
        body = response.json()
        data = _unwrap(body, "data") if "data" in body else body
        assert "email" in data or "role" in data
        print(f"\n✅ Barber GET /profile")

    def test_barber_can_update_profile(self, client: TestClient, barber_headers):
        response = client.put(
            "/api/profile",
            headers=barber_headers,
            json={
                "name": "Updated Barber Name",
                "bio": "Experienced barber with 10 years of practice",
                "specialization": ["Fade", "Beard Trim"]
            }
        )
        assert response.status_code in [200, 201], f"{response.status_code}: {response.text}"
        print(f"\n✅ Barber PUT /profile")

    def test_unauthenticated_cannot_access_profile(self, client: TestClient):
        response = client.get("/api/profile")
        assert response.status_code in [401, 403]
        print(f"\n✅ Access control: unauthenticated blocked from /profile")


# ============================================================================
# PORTFOLIO MODULE  /api/barber/portfolio
# ============================================================================

@pytest.mark.barber
class TestBarberPortfolio:
    """Barber portfolio CRUD"""

    def _create_work(self, client: TestClient, barber_headers):
        unique = int(time.time() * 1000)
        return client.post(
            "/api/barber/portfolio",
            headers=barber_headers,
            json={
                "title": f"Fade Cut {unique}",
                "description": "Classic fade",
                "before_image": "https://example.com/before.jpg",
                "after_image": "https://example.com/after.jpg",
                "tags": ["fade", "classic"]
            }
        )

    def test_barber_can_create_portfolio_work(self, client: TestClient, barber_headers):
        response = self._create_work(client, barber_headers)
        assert response.status_code in [200, 201], f"{response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data or "_id" in data or "work_id" in data
        print(f"\n✅ Barber created portfolio work")

    def test_barber_can_list_portfolio(self, client: TestClient, barber_headers):
        self._create_work(client, barber_headers)
        response = client.get("/api/barber/portfolio", headers=barber_headers)
        assert response.status_code == 200, f"{response.status_code}: {response.text}"
        data = response.json()
        # Returns list directly or wrapped
        works = data if isinstance(data, list) else _unwrap(data, "data", "works")
        assert isinstance(works, list)
        print(f"\n✅ Barber list portfolio: {len(works)} works")

    def test_barber_can_update_portfolio_work(self, client: TestClient, barber_headers):
        create = self._create_work(client, barber_headers)
        assert create.status_code in [200, 201]
        created = create.json()
        work_id = created.get("id") or created.get("_id") or created.get("work_id")
        if not work_id:
            pytest.skip("Could not extract work ID")

        resp = client.put(
            f"/api/barber/portfolio/{work_id}",
            headers=barber_headers,
            json={"title": "Updated Fade Cut", "description": "Updated description"}
        )
        assert resp.status_code in [200, 201], f"{resp.status_code}: {resp.text}"
        print(f"\n✅ Barber updated portfolio work {work_id}")

    def test_barber_can_delete_portfolio_work(self, client: TestClient, barber_headers):
        create = self._create_work(client, barber_headers)
        assert create.status_code in [200, 201]
        created = create.json()
        work_id = created.get("id") or created.get("_id") or created.get("work_id")
        if not work_id:
            pytest.skip("Could not extract work ID")

        resp = client.delete(f"/api/barber/portfolio/{work_id}", headers=barber_headers)
        assert resp.status_code in [200, 204], f"{resp.status_code}: {resp.text}"
        print(f"\n✅ Barber deleted portfolio work {work_id}")

    def test_public_portfolio_accessible(self, client: TestClient, barber_headers):
        self._create_work(client, barber_headers)
        profile = client.get("/api/profile", headers=barber_headers)
        assert profile.status_code == 200
        profile_data = _unwrap(profile.json(), "data")
        barber_id = (
            profile_data.get("id") or
            profile_data.get("_id") or
            profile_data.get("barber_id")
        )
        if not barber_id:
            pytest.skip("Could not determine barber ID")

        resp = client.get(f"/api/barber/portfolio/public/{barber_id}")
        assert resp.status_code in [200, 404], f"{resp.status_code}: {resp.text}"
        print(f"\n✅ Public portfolio endpoint reachable")

    def test_client_cannot_post_to_portfolio(self, client: TestClient, client_headers):
        response = client.post(
            "/api/barber/portfolio",
            headers=client_headers,
            json={
                "title": "Fake Work",
                "before_image": "https://example.com/before.jpg",
                "after_image": "https://example.com/after.jpg"
            }
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print(f"\n✅ Access control: client blocked from posting portfolio")


# ============================================================================
# BARBER SCHEDULE  /api/barbers/{id}/schedule
# ============================================================================

@pytest.mark.barber
class TestBarberSchedule:
    """Barber schedule GET/PUT"""

    def _get_barber_id(self, client: TestClient, barber_headers):
        profile = client.get("/api/profile", headers=barber_headers)
        assert profile.status_code == 200
        data = _unwrap(profile.json(), "data")
        # barber profile has barber sub-document; the barber ID might be in barber._id
        barber_doc = data.get("barber", {})
        return (
            barber_doc.get("_id") or
            barber_doc.get("id") or
            data.get("barber_id") or
            data.get("id") or
            data.get("_id")
        )

    def test_admin_can_get_barber_schedule(self, client: TestClient, admin_headers, barber_headers):
        barber_id = self._get_barber_id(client, barber_headers)
        if not barber_id:
            pytest.skip("Could not get barber ID")

        resp = client.get(f"/api/barbers/{barber_id}/schedule", headers=admin_headers)
        assert resp.status_code == 200, f"{resp.status_code}: {resp.text}"
        body = resp.json()
        # Response: list or {"success": True, "data": {"schedule": [...]}}
        if isinstance(body, list):
            data = body
        else:
            data = _unwrap(body, "data", "schedule")
            if not isinstance(data, list):
                data = []
        assert isinstance(data, list)
        print(f"\n✅ Admin GET barber schedule: {len(data)} days")

    def test_admin_can_update_barber_schedule(self, client: TestClient, admin_headers, barber_headers):
        barber_id = self._get_barber_id(client, barber_headers)
        if not barber_id:
            pytest.skip("Could not get barber ID")

        schedule = [
            {"day_of_week": i, "start_time": "09:00", "end_time": "18:00", "is_working": i < 5}
            for i in range(7)
        ]
        resp = client.put(
            f"/api/barbers/{barber_id}/schedule",
            headers=admin_headers,
            json={"schedule": schedule}
        )
        assert resp.status_code in [200, 201], f"{resp.status_code}: {resp.text}"
        print(f"\n✅ Admin updated barber schedule")

    def test_client_cannot_update_barber_schedule(self, client: TestClient, client_headers, barber_headers):
        barber_id = self._get_barber_id(client, barber_headers)
        if not barber_id:
            pytest.skip("Could not get barber ID")

        resp = client.put(
            f"/api/barbers/{barber_id}/schedule",
            headers=client_headers,
            json={"schedule": []}
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
        print(f"\n✅ Access control: client blocked from updating schedule")


# ============================================================================
# NOTIFICATIONS  /api/notifications
# ============================================================================

@pytest.mark.client
class TestNotifications:
    """Notification endpoints"""

    def test_client_can_list_notifications(self, client: TestClient, client_headers):
        response = client.get("/api/notifications", headers=client_headers)
        assert response.status_code == 200, f"{response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, (list, dict))
        print(f"\n✅ Client list notifications")

    def test_unauthenticated_cannot_access_notifications(self, client: TestClient):
        response = client.get("/api/notifications")
        assert response.status_code in [401, 403], \
            f"Expected 401/403, got {response.status_code}"
        print(f"\n✅ Access control: unauthenticated blocked from notifications")


# ============================================================================
# INTEGRATION WORKFLOWS
# ============================================================================

class TestIntegrationWorkflows:
    """End-to-end integration tests spanning multiple modules"""

    def test_admin_full_user_lifecycle(self, client: TestClient, admin_headers):
        """Admin creates, reads, updates, deletes a user"""
        unique = int(time.time() * 1000)
        email = f"lifecycle{unique}@example.com"

        create = client.post(
            "/api/users",
            headers=admin_headers,
            json={"email": email, "password": "Lifecycle@2026", "name": "Lifecycle User", "role": "client"}
        )
        assert create.status_code in [200, 201], f"Create: {create.text}"
        created = create.json()
        user = _unwrap(created, "data", "user")
        user_id = user.get("id") or user.get("_id")

        if user_id:
            read = client.get(f"/api/users/{user_id}", headers=admin_headers)
            assert read.status_code in [200, 201], f"Read: {read.text}"

            update = client.put(
                f"/api/users/{user_id}",
                headers=admin_headers,
                json={"name": "Updated Lifecycle"}
            )
            assert update.status_code in [200, 201], f"Update: {update.text}"

            delete = client.delete(f"/api/users/{user_id}", headers=admin_headers)
            assert delete.status_code in [200, 204], f"Delete: {delete.text}"

        print(f"\n✅ Admin full user lifecycle completed")

    def test_barber_portfolio_and_profile_workflow(self, client: TestClient, barber_headers):
        """Barber updates profile then adds a portfolio work"""
        profile_update = client.put(
            "/api/profile",
            headers=barber_headers,
            json={"bio": "Expert barber", "specialization": ["Fade", "Taper"]}
        )
        assert profile_update.status_code in [200, 201], f"Profile: {profile_update.text}"

        unique = int(time.time() * 1000)
        work = client.post(
            "/api/barber/portfolio",
            headers=barber_headers,
            json={
                "title": f"Workflow Cut {unique}",
                "description": "A perfect fade",
                "before_image": "https://example.com/b.jpg",
                "after_image": "https://example.com/a.jpg"
            }
        )
        assert work.status_code in [200, 201], f"Portfolio: {work.text}"

        portfolio = client.get("/api/barber/portfolio", headers=barber_headers)
        assert portfolio.status_code == 200
        works = portfolio.json()
        assert isinstance(works, list)
        assert len(works) >= 1
        print(f"\n✅ Barber profile + portfolio workflow completed")

    def test_admin_dashboard_reflects_created_data(self, client: TestClient, admin_headers):
        """Dashboard stats are consistent after creating users"""
        stats_before = client.get("/api/admin/dashboard/stats", headers=admin_headers)
        assert stats_before.status_code == 200
        before = _unwrap(stats_before.json(), "data") if "data" in stats_before.json() else stats_before.json()

        unique = int(time.time() * 1000)
        client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "email": f"dashtest{unique}@example.com",
                "password": "DashTest@2026",
                "name": "Dashboard Test User",
                "role": "client"
            }
        )

        stats_after = client.get("/api/admin/dashboard/stats", headers=admin_headers)
        assert stats_after.status_code == 200
        after = _unwrap(stats_after.json(), "data") if "data" in stats_after.json() else stats_after.json()

        if "total_clients" in before and "total_clients" in after:
            assert after["total_clients"] >= before["total_clients"]

        print(f"\n✅ Dashboard stats consistent")

    def test_role_access_matrix(self, client: TestClient, admin_headers, barber_headers, client_headers):
        """Verify role access matrix for new endpoints"""
        # (endpoint, method, {role: expected_status_or_list})
        checks = [
            ("/api/users",                   "GET", {"admin": 200, "barber": 403, "client": 403}),
            ("/api/admin/dashboard/stats",   "GET", {"admin": 200, "barber": 403, "client": 403}),
            ("/api/profile",                 "GET", {"admin": 200, "barber": 200, "client": 200}),
        ]
        headers_map = {
            "admin": admin_headers,
            "barber": barber_headers,
            "client": client_headers,
        }
        for endpoint, method, expected_by_role in checks:
            for role, expected in expected_by_role.items():
                headers = headers_map[role]
                if method == "GET":
                    resp = client.get(endpoint, headers=headers)
                else:
                    resp = client.post(endpoint, headers=headers, json={})

                if isinstance(expected, list):
                    assert resp.status_code in expected, (
                        f"Role={role} {method} {endpoint}: expected {expected}, got {resp.status_code}"
                    )
                else:
                    assert resp.status_code == expected, (
                        f"Role={role} {method} {endpoint}: expected {expected}, got {resp.status_code}: {resp.text}"
                    )
                print(f"  ✅ {role.upper():8} {method} {endpoint}: {resp.status_code}")

        print(f"\n✅ Full role access matrix verified")
