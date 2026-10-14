# -*- coding: utf-8 -*-
"""
Chatwork API adapter
"""
import requests
import time
from typing import List, Dict, Optional, Any
from datetime import datetime
import pytz

Vietnam_TZ = pytz.timezone("Asia/Ho_Chi_Minh")

class ChatworkAPIError(Exception):
    """Custom exception for Chatwork API errors"""
    def __init__(self, message: str, status_code: int = None, error_code: int = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


class ChatworkAdapter:
    """Adapter for Chatwork REST API v2"""

    BASE_URL = "https://api.chatwork.com/v2"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'X-ChatWorkToken': api_key,
            'Content-Type': 'application/json'
        })

    def _request(self, method: str, endpoint: str, params: Dict = None,
                 data: Dict = None, retry_count: int = 3) -> Dict:
        """Make API request with retry logic for rate limits"""
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"

        for attempt in range(retry_count):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    timeout=30
                )

                # Handle rate limiting
                if response.status_code == 429:
                    try:retry_after = max(1,min(120,int(response.headers.get('Retry-After',60))))
                    except ValueError:retry_after = 60
                    if attempt < retry_count - 1:
                        time.sleep(retry_after)
                        continue
                    raise ChatworkAPIError(
                        f"Rate limit exceeded. Retry after {retry_after} seconds.",
                        status_code=429
                    )

                # Handle success
                if response.status_code == 204:
                    return []
                if response.status_code == 200:
                    return response.json()

                # Handle errors
                if response.status_code == 401:
                    raise ChatworkAPIError(
                        "Invalid API key",
                        status_code=401
                    )
                elif response.status_code == 404:
                    raise ChatworkAPIError('Room không tồn tại hoặc không có quyền truy cập.',status_code=404)
                else:
                    error_data = {}
                    raise ChatworkAPIError(
                        error_data.get('errors', [f"HTTP {response.status_code}"])[0],
                        status_code=response.status_code
                    )

            except requests.exceptions.Timeout:
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise ChatworkAPIError("Request timeout after retries")
            except requests.exceptions.ConnectionError as e:
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise ChatworkAPIError(f"Connection error: {str(e)}")

        raise ChatworkAPIError("Max retries exceeded")

    def test_connection(self) -> Dict:
        """Test API connection"""
        result = self._request('GET', '/me')
        return {
            'account_id': result.get('account_id'),
            'name': result.get('name'),
            'chatwork_id': result.get('chatwork_id'),
            'organization_id': result.get('organization_id')
        }

    def get_rooms(self) -> List[Dict]:
        """Get all rooms the user has access to"""
        result = self._request('GET', '/rooms')
        return result if isinstance(result, list) else result.get('data', [])

    def get_room_info(self, room_id: str) -> Dict:
        """Get room information"""
        return self._request('GET', f'/rooms/{room_id}')

    def get_messages(self, room_id: str, force: bool = False,
                     params: Dict = None) -> List[Dict]:
        """
        Get messages from a room.

        Chatwork API returns up to 100 messages per request.

        Historical pagination is not supported. Only force is documented.

        Args:
            room_id: The Chatwork room ID
            force: If True, ignore cache
            params: Additional parameters (limit, message_id, etc.)

        Returns:
            List of messages (empty list when the API has no more history)
        """
        if params is None:
            params = {}

        # Default to 100 messages (API limit per request)
        params['force'] = 1 if force else 0

        result = self._request('GET', f'/rooms/{room_id}/messages', params=params)

        if isinstance(result, dict):
            return result.get('data', result.get('messages', []))
        return result if isinstance(result, list) else []

    def get_messages_before(self, room_id, before_message_id):
        raise ChatworkAPIError('Chatwork không hỗ trợ phân trang lịch sử bằng message_id. Cần nhập MessageLog đã lưu.')

    def get_messages_in_range(self, room_id, start_time, end_time):
        """Filter the recent window; never claim historical pagination."""
        page = self.get_recent_messages(room_id)
        if len(page) >= 100:
            earliest = min(m['send_time'] for m in page)
            if start_time.timestamp() < earliest:
                raise ChatworkAPIError('Khoảng cần lấy nằm ngoài 100 tin gần nhất. Cần nhập lịch sử MessageLog.')
        return [m for m in page if start_time.timestamp() <= m['send_time'] <= end_time.timestamp()]

    def get_recent_messages(self, room_id: str, limit: int = 100) -> List[Dict]:
        """Get the most recent messages from a room"""
        params = {}
        return self.get_messages(room_id, force=True, params=params)

    def normalize_message(self, raw_message: Dict) -> Dict:
        """Normalize Chatwork message format to internal format"""
        send_time_str = raw_message.get('send_time', raw_message.get('created_at', ''))

        # Parse send time
        if isinstance(send_time_str, (int, float)):
            send_time = datetime.fromtimestamp(send_time_str, Vietnam_TZ)
        elif send_time_str:
            try:
                if 'Z' in send_time_str:
                    send_time = datetime.fromisoformat(send_time_str.replace('Z', '+00:00'))
                else:
                    send_time = datetime.fromisoformat(send_time_str)
                # Convert to Vietnam timezone
                send_time = send_time.astimezone(Vietnam_TZ)
            except:
                raise ChatworkAPIError('Tin nhắn có thời gian không hợp lệ.')
        else:
            raise ChatworkAPIError('Tin nhắn thiếu thời gian gửi.')

        return {
            'message_id': str(raw_message.get('message_id', '')),
            'room_id': str(raw_message.get('room_id', '')),
            'account_id': raw_message.get('account', {}).get('account_id', raw_message.get('account_id')),
            'name': raw_message.get('account', {}).get('name', raw_message.get('name', '')),
            'body': raw_message.get('body', ''),
            'send_time': send_time.isoformat(),
            'updated_time': raw_message.get('update_time', '')
        }
