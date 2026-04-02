import hashlib
import logging
from datetime import datetime

import aiohttp

_LOGGER = logging.getLogger(__name__)


class ZTEConnectionError(Exception):
    """Raised when the router cannot be reached."""


class ZTEAuthError(Exception):
    """Raised when login credentials are rejected."""


class ZTERouterAPI:
    """Async wrapper for the ZTE Router goform API using aiohttp."""

    def __init__(self, session: aiohttp.ClientSession, ip, username, password):
        """Initialize the API."""
        self.session = session
        self.ip = ip
        self.username = username
        self.password = password
        self.protocol = "http"
        self.referer = f"http://{self.ip}/"
        self.timeout = aiohttp.ClientTimeout(total=15)
        self.stok = None

    def _hash(self, val):
        if val is None:
            raise ValueError("Input to hash function cannot be None")
        return hashlib.sha256(val.encode()).hexdigest()

    def _hex_decode(self, hex_str):
        if not hex_str:
            return ""
        decoded = ""
        try:
            for i in range(0, len(hex_str), 4):
                decoded += chr(int(hex_str[i : i + 4], 16))
            return decoded
        except Exception as e:
            _LOGGER.debug("Failed to decode hex string '%s': %s", hex_str, e)
            return "[Decoding Error]"

    def _parse_date(self, date_str):
        if not date_str:
            return None
        try:
            parts = date_str.split(",")
            if len(parts) >= 6:
                year = int(f"20{parts[0]}")
                month = int(parts[1])
                day = int(parts[2])
                hour = int(parts[3])
                minute = int(parts[4])
                second = int(parts[5])
                dt = datetime(year, month, day, hour, minute, second)
                return dt.isoformat()
        except Exception as e:
            _LOGGER.debug("Failed to parse date string '%s': %s", date_str, e)
        return date_str

    async def try_set_protocol(self, timeout_sec=5):
        """Identify if router is on http or https with a short timeout."""
        protocols = ["http", "https"]
        tout = aiohttp.ClientTimeout(total=timeout_sec)
        for proto in protocols:
            url = f"{proto}://{self.ip}"
            try:
                # SSL verification is disabled as local routers use self-signed certs
                async with self.session.get(url, timeout=tout, ssl=False) as r:
                    if r.status < 400:
                        self.protocol = proto
                        self.referer = f"{self.protocol}://{self.ip}/"
                        return
            except Exception as e:
                _LOGGER.debug("Failed to connect via %s: %s", proto, e)

    async def get_version(self, timeout_sec=None):
        tout = aiohttp.ClientTimeout(total=timeout_sec) if timeout_sec else self.timeout
        url = (
            f"{self.referer}goform/goform_get_cmd_process"
            "?isTest=false&cmd=wa_inner_version"
        )
        try:
            async with self.session.get(
                url, headers={"Referer": self.referer}, timeout=tout, ssl=False
            ) as r:
                data = await r.json(content_type=None)
                return data.get("wa_inner_version", "")
        except Exception as e:
            _LOGGER.debug("Failed to get version: %s", e)
            return ""

    async def get_LD(self, timeout_sec=None):
        tout = aiohttp.ClientTimeout(total=timeout_sec) if timeout_sec else self.timeout
        url = f"{self.referer}goform/goform_get_cmd_process?isTest=false&cmd=LD"
        try:
            async with self.session.get(
                url, headers={"Referer": self.referer}, timeout=tout, ssl=False
            ) as r:
                data = await r.json(content_type=None)
                return data.get("LD", "").upper()
        except Exception as e:
            raise ZTEConnectionError(f"Failed to reach router: {e}") from e

    async def login(self, timeout_sec=None):
        """Clean login that resets the internal session state."""
        tout = timeout_sec or 15
        self.stok = None

        ld = await self.get_LD(timeout_sec=tout)
        version = await self.get_version(timeout_sec=tout)

        if not self.password:
            raise Exception("No password provided")
        pass_hash = self._hash(self.password).upper()
        zte_pass = self._hash(pass_hash + ld).upper()

        is_multi = True
        if version and any(m in version for m in ["MC801", "MC7010"]):
            is_multi = False

        payload = {
            "isTest": "false",
            "goformId": "LOGIN"
            if (self.username and not is_multi)
            else "LOGIN_MULTI_USER",
            "password": zte_pass,
        }
        if self.username:
            payload["username"] = self.username

        url = f"{self.referer}goform/goform_set_cmd_process"
        try:
            async with self.session.post(
                url,
                data=payload,
                headers={"Referer": self.referer},
                timeout=aiohttp.ClientTimeout(total=tout),
                ssl=False,
            ) as r:
                stok = r.cookies.get("stok")
                if not stok:
                    _LOGGER.error(
                        "Login failed: missing stok in response. Status: %s", r.status
                    )
                    raise ZTEAuthError("Login failed")

                self.stok = f"stok={stok.value.strip('"')}"
                return self.stok
        except Exception as e:
            if isinstance(e, ZTEAuthError):
                raise
            raise ZTEConnectionError(
                f"Login failed due to connection error: {e}"
            ) from e

    async def get_all_data(self):
        """Fetch primary technical data."""
        if not self.stok:
            await self.login()

        params = [
            "cell_id",
            "lan_ipaddr",
            "lte_ca_pcell_band",
            "lte_ca_pcell_bandwidth",
            "lte_ca_scell_band",
            "lte_ca_scell_bandwidth",
            "lte_pci",
            "lte_rsrp",
            "lte_rsrq",
            "lte_rssi",
            "lte_snr",
            "mdm_mcc",
            "mdm_mnc",
            "monthly_rx_bytes",
            "monthly_tx_bytes",
            "network_provider",
            "network_type",
            "nr5g_action_band",
            "nr5g_action_channel",
            "nr5g_pci",
            "realtime_time",
            "rmcc",
            "rmnc",
            "signalbar",
            "wan_active_band",
            "wan_active_channel",
            "wan_apn",
            "wan_connect_status",
            "wan_ipaddr",
            "wan_lte_ca",
            "wa_inner_version",
            "Z5g_rsrp",
            "Z5g_SINR",
            "rssi",
            "rscp",
            "sms_unread_num",
            "sms_received_flag",
            "sms_nv_rev_total",
            "sms_nv_send_total",
            "sms_nv_draftbox_total",
            "sms_sim_rev_total",
            "sms_sim_send_total",
            "sms_sim_draftbox_total",
            "sms_nv_total",
            "sms_sim_total",
        ]
        cmd = ",".join(params)
        url = (
            f"{self.referer}goform/goform_get_cmd_process"
            f"?multi_data=1&isTest=false&sms_received_flag_flag=0&cmd={cmd}"
        )
        headers = {"Referer": f"{self.referer}index.html", "Cookie": self.stok}
        try:
            async with self.session.get(
                url, headers=headers, timeout=self.timeout, ssl=False
            ) as r:
                data = await r.json(content_type=None)

                # Session expired check (router returns empty strings for core keys)
                if data.get("network_type") == "" and data.get("signalbar") == "":
                    await self.login()
                    return await self.get_all_data()
                return data
        except Exception as e:
            _LOGGER.error("Failed to fetch all data: %s", e)
            self.stok = None
            raise

    async def get_sms_capacity(self, timeout_sec=None):
        tout = aiohttp.ClientTimeout(total=timeout_sec) if timeout_sec else self.timeout
        if not self.stok:
            await self.login()
        url = (
            f"{self.referer}goform/goform_get_cmd_process"
            "?isTest=false&cmd=sms_capacity_info"
        )
        headers = {"Referer": f"{self.referer}index.html", "Cookie": self.stok}
        try:
            async with self.session.get(
                url, headers=headers, timeout=tout, ssl=False
            ) as r:
                return await r.json(content_type=None)
        except Exception as e:
            _LOGGER.debug("Failed to get SMS capacity: %s", e)
            return {}

    async def get_last_sms_content(self, timeout_sec=None):
        tout = aiohttp.ClientTimeout(total=timeout_sec) if timeout_sec else self.timeout
        if not self.stok:
            await self.login()
        url = f"{self.referer}goform/goform_get_cmd_process"
        payload = {
            "isTest": "false",
            "cmd": "sms_data_total",
            "page": "0",
            "data_per_page": "1",
            "mem_store": "1",
            "tags": "10",
            "order_by": "order by id desc",
        }
        headers = {"Referer": f"{self.referer}index.html", "Cookie": self.stok}
        try:
            async with self.session.post(
                url, data=payload, headers=headers, timeout=tout, ssl=False
            ) as r:
                resp_json = await r.json(content_type=None)
                messages = resp_json.get("messages", [])
                if messages:
                    msg = messages[0]
                    msg["content_decoded"] = self._hex_decode(msg.get("content", ""))
                    msg["number_decoded"] = self._hex_decode(msg.get("number", ""))
                    msg["date_decoded"] = self._parse_date(msg.get("date", ""))
                    return msg
                return {}
        except Exception as e:
            _LOGGER.debug("Failed to get last SMS content: %s", e)
            return {}

    async def reboot(self):
        """Execute a device reboot."""
        try:
            await self.login()
            ad = await self.get_AD()
            payload = f"isTest=false&goformId=REBOOT_DEVICE&AD={ad}"
            headers = {
                "Referer": self.referer,
                "Cookie": self.stok,
                "Content-Type": "application/x-www-form-urlencoded",
            }
            url = f"{self.referer}goform/goform_set_cmd_process"
            async with self.session.post(
                url, headers=headers, data=payload, timeout=self.timeout, ssl=False
            ) as r:
                return r.status
        except Exception as e:
            _LOGGER.error("Failed to execute reboot: %s", e)
            self.stok = None
            raise

    async def delete_sms(self, msg_id):
        """Helper to delete SMS."""
        if not self.stok:
            await self.login()
        ad = await self.get_AD()
        payload = f"isTest=false&goformId=DELETE_SMS&msg_id={msg_id}&AD=" + ad
        headers = {
            "Referer": self.referer,
            "Cookie": self.stok,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        url = f"{self.referer}goform/goform_set_cmd_process"
        async with self.session.post(
            url, headers=headers, data=payload, timeout=self.timeout, ssl=False
        ) as r:
            return r.status

    async def delete_all(self):
        """Action Button Logic to delete all SMS."""
        try:
            await self.login()
            url = f"{self.referer}goform/goform_get_cmd_process"
            payload = {
                "isTest": "false",
                "cmd": "sms_data_total",
                "page": "0",
                "data_per_page": "500",
                "mem_store": "1",
                "tags": "10",
                "order_by": "order by id desc",
            }
            headers = {"Referer": f"{self.referer}index.html", "Cookie": self.stok}
            async with self.session.post(
                url, data=payload, headers=headers, timeout=self.timeout, ssl=False
            ) as r:
                resp_json = await r.json(content_type=None)
                ids = [m["id"] for m in resp_json.get("messages", [])]

            if ids:
                return await self.delete_sms(";".join(ids))
            return 200
        except Exception as e:
            _LOGGER.error("Failed to delete all SMS: %s", e)
            self.stok = None
            raise

    async def get_AD(self, timeout_sec=None):
        version = await self.get_version(timeout_sec=timeout_sec)
        if not version:
            return ""
        is_new_gen = any(m in version for m in ["MC888", "MC889"])
        hash_func = (
            (lambda s: hashlib.sha256(s.encode()).hexdigest().upper())
            if is_new_gen
            else (lambda s: hashlib.md5(s.encode()).hexdigest())
        )
        a = hash_func(version)
        rd = await self.get_RD(timeout_sec=timeout_sec)
        return hash_func(a + rd)

    async def get_RD(self, timeout_sec=None):
        tout = aiohttp.ClientTimeout(total=timeout_sec) if timeout_sec else self.timeout
        url = f"{self.referer}goform/goform_get_cmd_process?isTest=false&cmd=RD"
        headers = {"Referer": f"{self.referer}index.html", "Cookie": self.stok}
        try:
            async with self.session.get(
                url, headers=headers, timeout=tout, ssl=False
            ) as r:
                data = await r.json(content_type=None)
                return data.get("RD", "")
        except Exception as e:
            _LOGGER.debug("Failed to get RD: %s", e)
            return ""
