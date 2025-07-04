import socket
import ssl
import asyncio
import httpx
import platform
import subprocess
import ipaddress
from typing import List, Optional, Set, Dict
from ipwhois import IPWhois

from .sources import get_active_sources, get_ip_sources, get_static_ip_ranges

# رنگ‌ها برای چاپ ترمینال
# Terminal color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
PURPLE = "\033[95m"
GRAY = "\033[90m"
RESET = "\033[0m"

# کلاس پایه برای اسکن با قابلیت کنترل همزمانی (concurrency)
# Base scanner class with async concurrency handling
class BaseScanner:
    def __init__(self, concurrency: int = 20):
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(concurrency)

    async def fetch_list_from_url(self, client: httpx.AsyncClient, url: str) -> Set[str]:
        """
        دریافت لیست آیتم‌ها از URL
        Fetch list of items (domains or IPs) from a given URL
        """
        try:
            resp = await client.get(url, timeout=10)
            resp.raise_for_status()
            items = {
                line.strip()
                for line in resp.text.splitlines()
                if line.strip() and not line.startswith("#")
            }
            print(f"{YELLOW}[+] Fetched {GREEN}{len(items)} items from {GRAY}{url}")
            return items
        except Exception as e:
            print(f"{RED}[!] Failed to fetch from {YELLOW}{url}{RED}: {e}")
            return set()

    async def fetch_all_from_sources(self, sources: List[str], progress: Optional[Dict] = None) -> List[str]:
        """
        دریافت تمام آیتم‌ها از منابع داده شده
        Fetch all unique items from a list of source URLs
        """
        async with httpx.AsyncClient(verify=True) as client:
            all_items = set()
            for url in sources:
                if progress and progress.get("cancel"):
                    print("[!] Scan canceled before fetching all sources.")
                    break
                items = await self.fetch_list_from_url(client, url)
                all_items.update(items)

            result = list(all_items)
            if progress is not None:
                progress["total"] = len(result)
                progress["done"] = 0
                progress["results"] = []

            print(f"[=] Total unique items fetched: {len(result)}")
            return result

    async def scan_items(self, items: List[str], progress: Optional[Dict] = None) -> List[str]:
        raise NotImplementedError("Subclasses must implement scan_items method.")


# ---------------------- اسکنر دامنه (Reality) ----------------------
class DomainScanner(BaseScanner):
    def __init__(self, concurrency: int = 20):
        super().__init__(concurrency)

    def is_domain_alive(self, domain: str, timeout=3) -> bool:
        """
        بررسی روشن بودن دامنه (TLS handshake)
        Check if domain is alive via TLS handshake
        """
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=timeout) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    return bool(ssock.getpeercert())
        except Exception:
            return False

    async def check_domain_not_blocked_from_iran(self, domain: str) -> bool:
        """
        بررسی دسترسی دامنه از ایران (با فرض اجرای این کد از داخل ایران)
        Check if domain is reachable from Iran (based on local IP access)
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"https://{domain}", follow_redirects=True)
                return r.status_code == 200
        except Exception:
            return False

    async def check_domain_async(self, domain: str) -> Optional[str]:
        """
        بررسی دامنه به صورت async همراه با بررسی فیلتر نبودن
        Check domain: TLS & access from Iran
        """
        async with self.semaphore:
            loop = asyncio.get_running_loop()
            alive = await loop.run_in_executor(None, self.is_domain_alive, domain)
            if alive:
                iran_access = await self.check_domain_not_blocked_from_iran(domain)
                if iran_access:
                    print(f"{GREEN}[+] Domain {PURPLE}{domain} {GREEN}is alive and accessible from IR")
                    return domain
                else:
                    print(f"{RED}[-] Domain {YELLOW}{domain} {RED}is blocked from Iran")
                    return None
            else:
                print(f"{GRAY}[-] Domain {YELLOW}{domain} {GRAY}is not reachable")
                return None

    async def scan_items(self, domains: List[str], progress: Optional[Dict] = None) -> List[str]:
        """
        اجرای اسکن برای لیست دامنه‌ها
        Scan list of domains and return valid/clean ones
        """
        clean = []
        for domain in domains:
            if progress and progress.get("cancel"):
                print(f"{PURPLE}[!] Scan canceled by user.")
                break
            result = await self.check_domain_async(domain)
            if result:
                clean.append(result)
                if progress is not None:
                    progress["results"].append(result)
            if progress is not None:
                progress["done"] += 1
        return clean


# تابع کمک برای اسکن دستی دامنه‌ها
async def scan_manual_domains(domains: List[str], concurrency: int = 20) -> List[str]:
    scanner = DomainScanner(concurrency)
    return await scanner.scan_items(domains)


# تابع کمک برای اسکن خودکار دامنه‌های Reality
async def get_reality_domains(progress: Optional[Dict] = None, concurrency: int = 20) -> List[str]:
    scanner = DomainScanner(concurrency)
    sources = get_active_sources()
    domains = await scanner.fetch_all_from_sources(sources, progress=progress)
    return await scanner.scan_items(domains, progress=progress)

# ---------------------- اسکنر IP (Fastly / Cloudflare) ----------------------

class IPCleanScanner(BaseScanner):
    def __init__(self, concurrency: int = 20, test_port: int = 443, timeout: int = 3):
        super().__init__(concurrency)
        self.test_port = test_port
        self.timeout = timeout

    def is_ip_alive(self, ip: str) -> bool:
        """
        بررسی باز بودن پورت 443 (به صورت sync)
        Check if IP is reachable on port 443
        """
        try:
            with socket.create_connection((ip, self.test_port), timeout=self.timeout):
                return True
        except Exception:
            return False

    async def check_ip_async(self, ip: str) -> Optional[str]:
        """
        بررسی async برای IP
        Async check if IP is alive
        """
        async with self.semaphore:
            loop = asyncio.get_running_loop()
            alive = await loop.run_in_executor(None, self.is_ip_alive, ip)
            if alive:
                print(f"{CYAN}[+] IP {ip} is reachable")
                return ip
            else:
                print(f"{GRAY}[-] IP {ip} is NOT reachable")
                return None

    async def scan_items(self, ips: List[str], progress: Optional[Dict] = None) -> List[str]:
        """
        اسکن مجموعه‌ای از IPها
        Scan a list of IPs and return those reachable
        """
        clean = []
        for ip in ips:
            if progress and progress.get("cancel"):
                print("[!] Scan canceled by user.")
                break
            result = await self.check_ip_async(ip)
            if result:
                clean.append(result)
                if progress is not None:
                    progress["results"].append(result)
            if progress is not None:
                progress["done"] += 1
        return clean


# ---------------------- توابع بررسی پاک بودن IP ----------------------

FASTLY_DOMAINS = [
    "github.com", 
    "cdn.jsdelivr.net", 
    "assets-cdn.github.com",
    "global.prod.fastly.net"
]

CLOUDFLARE_DOMAINS = [
    "www.cloudflare.com",
    "www.cloudflarestatus.com",
    "www.cloudflareinsights.com",
    "1.1.1.1",
    "blog.cloudflare.com",
    "developers.cloudflare.com",
    "workers.cloudflare.com",
    "pages.dev",
    "cf.pages.dev",
    "status.cloudflare.com"
]

async def ping_ip(ip: str, count: int = 1, timeout: int = 1) -> bool:
    """
    پینگ IP و بررسی پاسخ
    Ping an IP and check response
    """
    system = platform.system().lower()
    ping_cmd = (
        ["ping", "-c", str(count), "-t", str(timeout), ip] if system == "darwin"
        else ["ping", "-c", str(count), "-W", str(timeout), ip]
    )

    loop = asyncio.get_running_loop()
    try:
        output = await loop.run_in_executor(
            None,
            lambda: subprocess.check_output(ping_cmd, stderr=subprocess.DEVNULL).decode()
        )
        return "bytes from" in output or "icmp_seq" in output
    except Exception as e:
        print(f"[!] ping failed for {ip}: {e}")
        return False


def check_whois(ip: str, provider_name: str) -> bool:
    """
    بررسی مالکیت IP با WHOIS
    Check IP ownership via WHOIS for provider match
    """
    try:
        obj = IPWhois(ip)
        res = obj.lookup_rdap()
        asn_desc = res.get('asn_description', '').lower()
        org_name = res.get('network', {}).get('name', '').lower()
        provider_name = provider_name.lower()
        return provider_name in asn_desc or provider_name in org_name
    except Exception:
        return False


def check_tcp_port(ip: str, port=443, timeout=2) -> bool:
    """
    بررسی باز بودن پورت TCP
    Check if given TCP port is open
    """
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except Exception:
        return False


async def check_tls_sni(ip: str, domain_list: list, timeout=3) -> bool:
    """
    بررسی TLS handshake با SNI برای یک لیست دامنه
    Check TLS handshake using SNI for list of domains
    """
    for domain in domain_list:
        try:
            context = ssl.create_default_context()
            with socket.create_connection((ip, 443), timeout=timeout) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    if ssock.getpeercert():
                        print(f"{GREEN}[✓] TLS success for {ip} with {domain}")
                        return True
        except Exception as e:
            print(f"{RED}[✗] TLS failed for {ip} with {domain}: {e}")
    return False


async def is_ip_clean(ip: str, provider: str, use_tls_check: bool = True) -> bool:
    """
    بررسی کامل پاک بودن IP (مالکیت، پینگ، پورت، TLS)
    Full check for IP cleanliness
    """
    domains = FASTLY_DOMAINS if provider == "fastly" else CLOUDFLARE_DOMAINS

    if not check_whois(ip, provider):
        print(f"{RED}[-] {ip} rejected: WHOIS mismatch")
        return False
    print(f"{GREEN}[✓] WHOIS OK for {ip}")

    if not await ping_ip(ip):
        print(f"{RED}[-] {ip} rejected: ping failed")
        return False
    print(f"{GREEN}[✓] Ping OK for {ip}")

    if not check_tcp_port(ip):
        print(f"{RED}[-] {ip} rejected: TCP port closed")
        return False
    print(f"{GREEN}[✓] TCP port OK for {ip}")

    if use_tls_check:
        if not await check_tls_sni(ip, domains):
            print(f"{RED}[-] {ip} rejected: TLS SNI failed")
            return False
        print(f"{GREEN}[✓] TLS OK for {ip}")

    print(f"{PURPLE}[✔] {ip} is clean and usable")
    return True

def ping_latency(ip: str, count: int = 1, timeout: int = 1) -> float:
    """
    اندازه‌گیری latency پینگ برای مرتب‌سازی
    Measure ping latency for an IP (used for sorting clean IPs)
    """
    system = platform.system()
    try:
        if system == "Darwin":  # macOS
            output = subprocess.check_output(
                ["ping", "-c", str(count), "-t", str(timeout), ip],
                stderr=subprocess.DEVNULL
            ).decode()
        elif system == "Windows":
            output = subprocess.check_output(
                ["ping", "-n", str(count), "-w", str(timeout * 1000), ip],
                stderr=subprocess.DEVNULL
            ).decode()
        else:  # Linux
            output = subprocess.check_output(
                ["ping", "-c", str(count), "-W", str(timeout), ip],
                stderr=subprocess.DEVNULL
            ).decode()

        for line in output.splitlines():
            if "time=" in line.lower():
                part = line.lower().split("time=")[1]
                time_str = "".join(c for c in part if (c.isdigit() or c == "."))
                return float(time_str)
        return float("inf")
    except Exception as e:
        print(f"[!] ping latency failed for {ip} on {system}: {e}")
        return float("inf")


async def get_clean_ips_with_lowest_ping(
    provider: str,
    required_count: int = 2,
    overfetch_factor: float = 2.5,
    progress: Optional[Dict] = None,
    concurrency: int = 20,
    use_tls_check: bool = True,
) -> List[str]:
    """
    دریافت IPهای تمیز با کمترین پینگ
    Get clean IPs with lowest latency from Fastly/Cloudflare sources
    """
    progress = progress or {}
    progress.setdefault("results", [])
    progress.setdefault("done", 0)
    progress.setdefault("cancel", False)
    progress.setdefault("total", 0)

    ips = set()

    # مرحله ➊: دریافت IPها از CIDR استاتیک
    for cidr in get_static_ip_ranges(provider):
        try:
            net = ipaddress.IPv4Network(cidr, strict=False)
            ips.update(str(ip) for ip in net)
        except Exception as e:
            print(f"[!] Invalid CIDR {cidr}: {e}")

    # مرحله ➋: دریافت IP از منابع آنلاین
    scanner = IPCleanScanner(concurrency)
    sources = get_ip_sources(provider)
    async with httpx.AsyncClient() as client:
        for url in sources:
            if progress.get("cancel"):
                print("[!] Scan canceled during fetching sources.")
                return []
            fetched = await scanner.fetch_list_from_url(client, url)
            ips.update(fetched)

    ip_list = list(ips)
    max_needed = int(required_count * overfetch_factor)
    progress["total"] = len(ip_list)

    clean_ips = []
    sem = asyncio.Semaphore(concurrency)
    should_stop = False

    # تابع داخلی برای بررسی هر IP
    async def check_ip(ip: str):
        async with sem:
            if progress.get("cancel") or should_stop:
                return None
            try:
                alive = await scanner.check_ip_async(ip)
                if not alive:
                    return None
                clean = await is_ip_clean(ip, provider, use_tls_check=use_tls_check)
                if clean:
                    return ip
            except Exception:
                return None
            return None

    tasks = [asyncio.create_task(check_ip(ip)) for ip in ip_list]

    try:
        for task in asyncio.as_completed(tasks):
            if progress.get("cancel"):
                should_stop = True
                print("[!] Cancel requested. Stopping early...")
                break

            ip = await task
            progress["done"] += 1

            if ip:
                clean_ips.append(ip)
                progress["results"].append(ip)
                if len(clean_ips) >= max_needed:
                    should_stop = True
                    print("[√] Enough clean IPs found. Stopping early.")
                    break
    finally:
        # اطمینان از اینکه همه taskهای باقی‌مانده کنسل شوند
        for t in tasks:
            if not t.done():
                t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    # مرتب‌سازی بر اساس latency
    clean_ips = sorted(clean_ips, key=lambda ip: ping_latency(ip))[:required_count]

    return clean_ips


async def scan_manual_ips(
    ips: List[str],
    provider: str,
    use_tls_check: bool = True,
    concurrency: int = 20
) -> List[str]:
    """
    اسکن دستی لیست IP برای تعیین تمیز بودن
    Manual scan of IP list for validity
    """
    clean = []
    sem = asyncio.Semaphore(concurrency)
    scanner = IPCleanScanner(concurrency)

    async def check_ip(ip: str) -> Optional[str]:
        async with sem:
            alive = await scanner.check_ip_async(ip)
            if not alive:
                return None
            clean_ip = await is_ip_clean(ip, provider, use_tls_check=use_tls_check)
            if clean_ip:
                return ip
            return None

    tasks = [asyncio.create_task(check_ip(ip)) for ip in ips]
    for task in asyncio.as_completed(tasks):
        result = await task
        if result:
            clean.append(result)
    return clean
