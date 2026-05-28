import os
import pytest
import httpx

ADMIN_TOKEN = os.getenv('ADMIN_TEST_TOKEN')
BASE = os.getenv('API_BASE', 'http://localhost:9080')

pytestmark = pytest.mark.asyncio


@pytest.mark.skipif(not ADMIN_TOKEN, reason='ADMIN_TEST_TOKEN not provided')
async def test_create_user_and_client():
    headers = {'Authorization': f'Bearer {ADMIN_TOKEN}', 'Content-Type': 'application/json'}
    async with httpx.AsyncClient() as client:
        # create user
        user_payload = {
            'name': 'TestFlow Auto',
            'email': 'testflow_auto@example.com',
            'phone': '5550000',
            'password': 'Test!2345',
            'role': 'client'
        }
        r = await client.post(f'{BASE}/api/users', json=user_payload, headers=headers, timeout=10)
        assert r.status_code in (200,201)
        data = r.json()
        user_id = data.get('data', {}).get('user', {}).get('_id')
        assert user_id

        # create client profile
        client_payload = {'user_id': user_id, 'is_vip': False, 'address': '', 'city': ''}
        r2 = await client.post(f'{BASE}/api/clients', json=client_payload, headers=headers, timeout=10)
        assert r2.status_code in (200,201)
        data2 = r2.json()
        assert data2.get('success') is True

        # cleanup note: tests do not delete by default
