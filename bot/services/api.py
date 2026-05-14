"""
HTTP client for communicating with the Django backend.
All bot<->backend communication goes through this module.

Connection notes:
- In Docker: BACKEND_URL=http://backend:8000  (service name from docker-compose)
- Locally:   BACKEND_URL=http://localhost:8000
"""

from __future__ import annotations

import asyncio
import os
import logging
from typing import Optional, Union

import aiohttp

BACKEND_URL = os.environ.get('BACKEND_URL', 'https://salvation-alone-oppressed.ngrok-free.dev')
API_BASE = f'{BACKEND_URL}/api'

# Shared persistent session — создаётся один раз, не пересоздаётся на каждый запрос
_session: Optional[aiohttp.ClientSession] = None

# Таймаут на каждый запрос (сек)
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)

logger = logging.getLogger(__name__)


def _get_session() -> aiohttp.ClientSession:
    """Возвращает (или создаёт) общую aiohttp-сессию."""
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(timeout=REQUEST_TIMEOUT)
    return _session


async def close_session() -> None:
    """Вызывается при shutdown бота для корректного закрытия сессии."""
    global _session
    if _session and not _session.closed:
        await _session.close()
        _session = None


async def wait_for_backend(retries: int = 20, delay: float = 3.0) -> bool:
    """
    Ждёт доступности backend перед стартом reminder loop.
    Делает retries попыток с паузой delay секунд между ними.
    Возвращает True если backend ответил, False если исчерпаны попытки.
    """
    url = f'{BACKEND_URL}/api/houses/'
    logger.info('Waiting for backend at %s ...', BACKEND_URL)
    for attempt in range(1, retries + 1):
        try:
            session = _get_session()
            async with session.get(url) as r:
                if r.status < 500:
                    logger.info('Backend is up after %d attempt(s)', attempt)
                    return True
        except aiohttp.ClientConnectorError as e:
            logger.warning('Backend not reachable (attempt %d/%d): %s', attempt, retries, e)
        except Exception as e:
            logger.warning('Backend check error (attempt %d/%d): %s', attempt, retries, e)
        await asyncio.sleep(delay)

    logger.error('Backend did not become available after %d attempts. Giving up.', retries)
    return False


async def _get(path: str, params: dict = None) -> Optional[Union[dict, list]]:
    session = _get_session()
    try:
        async with session.get(f'{API_BASE}{path}', params=params) as r:
            if r.status == 200:
                return await r.json()
            logger.error('GET %s -> %s', path, r.status)
            return None
    except aiohttp.ClientConnectorError as e:
        logger.error('GET %s -- cannot connect to backend: %s', path, e)
        return None
    except asyncio.TimeoutError:
        logger.error('GET %s -- request timed out', path)
        return None
    except Exception as e:
        logger.error('GET %s error: %s', path, e)
        return None


async def _post(path: str, data: dict) -> Optional[dict]:
    session = _get_session()
    try:
        async with session.post(f'{API_BASE}{path}', json=data) as r:
            result = await r.json()
            if r.status in (200, 201):
                return result
            logger.error('POST %s -> %s: %s', path, r.status, result)
            return {'error': result.get('error', 'Ошибка сервера')}
    except aiohttp.ClientConnectorError as e:
        logger.error('POST %s -- cannot connect to backend: %s', path, e)
        return {'error': 'Сервер недоступен. Попробуйте позже.'}
    except asyncio.TimeoutError:
        logger.error('POST %s -- request timed out', path)
        return {'error': 'Сервер не отвечает. Попробуйте позже.'}
    except Exception as e:
        logger.error('POST %s error: %s', path, e)
        return {'error': 'Внутренняя ошибка. Попробуйте позже.'}


# ── Users ─────────────────────────────────────────────────────────────────────

async def register_or_get_user(telegram_id: int, username: str, full_name: str,
                                referral_code: Optional[str] = None) -> dict:
    return await _post('/users/register/', {
        'telegram_id': telegram_id,
        'username': username or '',
        'full_name': full_name,
        'referral_code': referral_code or '',
    })


async def get_user(telegram_id: int) -> Optional[dict]:
    return await _get(f'/users/by-telegram-id/{telegram_id}/')


# ── Houses ────────────────────────────────────────────────────────────────────

async def get_houses(page: int = 1) -> Optional[dict]:
    return await _get('/houses/', params={'page': page})


async def get_house(house_id: int) -> Optional[dict]:
    return await _get(f'/houses/{house_id}/')


async def get_house_availability(house_id: int) -> list:
    data = await _get(f'/houses/{house_id}/availability/')
    return data or []


# ── Bookings ──────────────────────────────────────────────────────────────────

async def calculate_price(telegram_id: int, house_id: int, start_date: str,
                           end_date: str, service_ids: list, promo_code: str = '') -> dict:
    return await _post('/bookings/calculate-price/', {
        'telegram_id': telegram_id,
        'house_id': house_id,
        'start_date': start_date,
        'end_date': end_date,
        'service_ids': service_ids,
        'promo_code': promo_code,
    })


async def create_booking(telegram_id: int, house_id: int, start_date: str,
                          end_date: str, service_ids: list, promo_code: str = '') -> dict:
    return await _post('/bookings/', {
        'telegram_id': telegram_id,
        'house_id': house_id,
        'start_date': start_date,
        'end_date': end_date,
        'service_ids': service_ids,
        'promo_code': promo_code,
    })


async def get_user_bookings(telegram_id: int) -> list:
    data = await _get('/bookings/', params={'telegram_id': telegram_id})
    if data and isinstance(data, dict):
        return data.get('results', [])
    return data or []


async def get_booking(booking_id: int) -> Optional[dict]:
    return await _get(f'/bookings/{booking_id}/')


async def cancel_booking(booking_id: int, telegram_id: int, reason: str = '') -> dict:
    return await _post(f'/bookings/{booking_id}/cancel/', {
        'telegram_id': telegram_id,
        'reason': reason,
    })


async def checkin_booking(booking_id: int) -> dict:
    return await _post(f'/bookings/{booking_id}/checkin/', {})


# ── Payments ──────────────────────────────────────────────────────────────────

async def process_payment(booking_id: int, telegram_id: int,
                           payment_type: str, telegram_payment_id: str = '') -> dict:
    return await _post('/payments/process/', {
        'booking_id': booking_id,
        'telegram_id': telegram_id,
        'payment_type': payment_type,
        'telegram_payment_id': telegram_payment_id,
    })


# ── Promos ────────────────────────────────────────────────────────────────────

async def check_promo(code: str) -> dict:
    return await _post('/promos/check/', {'code': code})
