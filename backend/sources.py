import os
import json
from typing import List, Dict, Set

# مسیر فایل منابع دامنه و IP
# Paths to domain and IP source files
DOMAIN_DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "domain_sources.json")
IP_DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "ip_sources.json")

# مسیر فایل‌های محدوده‌های IP ثابت برای Fastly و Cloudflare
# Paths to static CIDR range files for providers
IP_RANGE_FILES = {
    "fastly": os.path.join(os.path.dirname(__file__), "data", "fastly_ranges.json"),
    "cloudflare": os.path.join(os.path.dirname(__file__), "data", "cloudflare_ranges.json"),
}

# ایجاد دایرکتوری data و فایل‌های اولیه در صورت نبودن
# Create 'data' directory and initial JSON files if they don't exist
os.makedirs(os.path.dirname(DOMAIN_DATA_FILE), exist_ok=True)

for path in [DOMAIN_DATA_FILE, IP_DATA_FILE]:
    if not os.path.isfile(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f)

for path in IP_RANGE_FILES.values():
    if not os.path.isfile(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f)


# ------------------ مدیریت منابع دامنه (Reality Domains) ------------------

def load_domain_sources() -> List[Dict]:
    """
    بارگذاری لیست منابع دامنه از فایل
    Load the list of domain sources from JSON file
    """
    with open(DOMAIN_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_domain_sources(sources: List[Dict]):
    """
    ذخیره لیست منابع دامنه در فایل
    Save domain sources back to the JSON file
    """
    with open(DOMAIN_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(sources, f, indent=2, ensure_ascii=False)


def get_active_domain_sources() -> List[str]:
    """
    دریافت URL منابع فعال دامنه
    Get URLs of enabled domain sources
    """
    return [s["url"] for s in load_domain_sources() if s.get("enabled", True)]


def add_domain_source(url: str):
    """
    افزودن یک منبع دامنه جدید
    Add a new domain source
    """
    sources = load_domain_sources()
    if any(s["url"] == url for s in sources):
        raise ValueError("URL already exists")
    sources.append({"url": url, "enabled": True})
    save_domain_sources(sources)


def remove_domain_source(url: str):
    """
    حذف یک منبع دامنه
    Remove a domain source by URL
    """
    sources = [s for s in load_domain_sources() if s["url"] != url]
    save_domain_sources(sources)


def toggle_domain_source(url: str, enable: bool):
    """
    فعال یا غیرفعال کردن منبع دامنه
    Enable or disable a domain source
    """
    sources = load_domain_sources()
    for s in sources:
        if s["url"] == url:
            s["enabled"] = enable
            break
    else:
        raise ValueError("URL not found")
    save_domain_sources(sources)


# ------------------ مدیریت منابع IP (Fastly, Cloudflare, ...) ------------------

def load_ip_sources() -> List[Dict]:
    """
    بارگذاری منابع IP از فایل
    Load IP source list from JSON file
    """
    with open(IP_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_ip_sources(sources: List[Dict]):
    """
    ذخیره منابع IP در فایل
    Save IP sources to the JSON file
    """
    with open(IP_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(sources, f, indent=2, ensure_ascii=False)


def get_ip_sources(provider: str) -> List[str]:
    """
    دریافت URL منابع IP فعال برای یک provider خاص
    Get list of enabled IP source URLs for a given provider
    """
    return [
        s["url"]
        for s in load_ip_sources()
        if s.get("enabled", True) and s.get("provider", "").lower() == provider.lower()
    ]


def add_ip_source(url: str, provider: str):
    """
    افزودن منبع IP برای provider مشخص‌شده
    Add a new IP source with a specific provider
    """
    sources = load_ip_sources()
    if any(s["url"] == url for s in sources):
        raise ValueError("URL already exists")
    sources.append({"url": url, "enabled": True, "provider": provider})
    save_ip_sources(sources)


def remove_ip_source(url: str):
    """
    حذف یک منبع IP
    Remove an IP source by URL
    """
    sources = [s for s in load_ip_sources() if s["url"] != url]
    save_ip_sources(sources)


def toggle_ip_source(url: str, enable: bool):
    """
    فعال/غیرفعال کردن منبع IP
    Enable or disable an IP source
    """
    sources = load_ip_sources()
    for s in sources:
        if s["url"] == url:
            s["enabled"] = enable
            break
    else:
        raise ValueError("URL not found")
    save_ip_sources(sources)


def get_static_ip_ranges(provider: str) -> Set[str]:
    """
    دریافت رنج‌های IP استاتیک برای provider مشخص‌شده (از فایل JSON)
    Get static IP ranges for a specific provider from JSON file
    """
    path = IP_RANGE_FILES.get(provider.lower())
    if not path or not os.path.isfile(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        try:
            return set(json.load(f))
        except Exception:
            return set()


# شورت‌کات برای استفاده عمومی
# Shortcut alias
get_active_sources = get_active_domain_sources
