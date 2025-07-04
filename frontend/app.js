// متغیر پایه برای آدرس API (در صورت تغییر سرور کافی است فقط این را عوض کنید)
//const BASE_URL = "http://localhost:8000";
//برای استفاده local خط زیر را کامنت کنید و خط بالا را از کامنت خارج کنید
const BASE_URL = "https://mapsim-scanner-utility.onrender.com";

// انتخاب المان‌ها - دامنه‌ها
const autoBtn = document.getElementById("load-domains-auto-btn");
const cancelBtn = document.getElementById("cancel-auto-btn");
const autoStatus = document.getElementById("auto-status");
const manualBtn = document.getElementById("load-domains-manual-btn");
const manualInput = document.getElementById("manual-domains-input");
const domainList = document.getElementById("domain-list");
const downloadBtn = document.getElementById("download-clean-domains-btn");

// انتخاب المان‌ها - IPها
const ipTypeSelect = document.getElementById("ip-type-select");
const ipAutoBtn = document.getElementById("load-ips-auto-btn");
const ipCancelBtn = document.getElementById("cancel-ip-auto-btn");
const ipManualBtn = document.getElementById("load-ips-manual-btn");
const ipManualInput = document.getElementById("manual-ips-input");
const ipStatus = document.getElementById("ip-status");
const ipList = document.getElementById("ip-list");
const downloadIPsBtn = document.getElementById("download-clean-ips-btn");

// المان‌های پیشرفت کلی
const progressContainer = document.getElementById("progress-container");
const progressBar = document.getElementById("progress-bar");
const progressPercent = document.getElementById("progress-percent");

// انتخاب‌کننده تعداد IP تمیز لازم (اگر دارید، مقدار پیش‌فرض 2)
const requiredIpCountInput = document.getElementById("required-ip-count");

let autoScanInterval = null;
let ipScanInterval = null;

// دریافت موقعیت کاربر و هشدار غیر ایران
async function detectUserLocation() {
  try {
    const res = await fetch("https://ipwhois.app/json/");
    if (!res.ok) throw new Error("Failed to fetch IP info");
    const data = await res.json();

    const ip = data.ip || "نامشخص";
    const city = data.city || "نامشخص";
    const country = data.country || "نامشخص";

    const infoDiv = document.getElementById("user-ip-info");
    const warningDiv = document.getElementById("ip-warning");

    if (infoDiv) {
      infoDiv.textContent = `IP شما: ${ip} - موقعیت: ${city}، ${country}`;
    }

    if (warningDiv) {
      if (country.toLowerCase() !== "iran") {
        warningDiv.textContent = `⚠️ توجه: IP شما (${ip}) مربوط به کشور ${country} است و تست فیلترینگ ایران ممکن است دقیق نباشد. لطفاً برای بررسی دقیق‌تر، IP خود را به ایران تغییر دهید.`;
        warningDiv.style.color = "orange";
        warningDiv.style.fontWeight = "bold";
      } else {
        warningDiv.textContent = "";
      }
    }
  } catch (e) {
    console.error("خطا در دریافت اطلاعات IP:", e);
  }
}

async function checkServerStatus() {
  try {
    const res = await fetch(`${BASE_URL}/`);
    if (!res.ok) throw new Error();
  } catch {
    alert("⛔ ارتباط با سرور برقرار نیست. لطفاً از روشن بودن API اطمینان حاصل کنید.");
  }
}

window.addEventListener("load", () => {
  detectUserLocation();
  updateDownloadBtnState();
  checkServerStatus();
});

// --- دامنه‌ها ---

async function startAutoScan() {

  autoStatus.style.display = "block";
  ipStatus.style.display = "none";

  
  autoStatus.textContent = "وضعیت: در حال شروع اسکن...";
  autoBtn.disabled = true;
  cancelBtn.disabled = false;
  domainList.innerHTML = "<li>در حال اسکن دامنه‌ها...</li>";
  showProgress(0);

  try {
    const res = await fetch(`${BASE_URL}/clean-items/auto/start?type=reality`);
    const data = await res.json();
    if (data.status === "started") {
      autoStatus.textContent = "وضعیت: در حال اسکن...";
      autoScanInterval = setInterval(fetchAutoScanProgress, 2000);
    } else {
      throw new Error("اسکن قبلاً در حال انجام است");
    }
  } catch (e) {
    alert("خطا در شروع اسکن: " + e.message);
    resetProgress();
    autoBtn.disabled = false;
    cancelBtn.disabled = true;
  }
}

async function fetchAutoScanProgress() {
  try {
    const res = await fetch(`${BASE_URL}/clean-items/auto/progress?type=reality`);
    if (!res.ok) throw new Error("دریافت وضعیت اسکن ناموفق بود");
    const data = await res.json();

    let percent = 0;
    if (data.total && data.total > 0) {
      percent = Math.min(100, Math.round((data.done / data.total) * 100));
    }

    showProgress(percent);

    autoStatus.textContent = `وضعیت: ${data.running ? "در حال اسکن" : "پایان یافته"} - دامنه‌های پاک: ${data.results_count} از ${data.total}`;

    // نمایش دامنه‌ها
    domainList.innerHTML = "";
    if (data.results && data.results.length > 0) {
      data.results.forEach(domain => {
        const li = document.createElement("li");
        li.textContent = domain;
        domainList.appendChild(li);
      });
    } else {
      domainList.innerHTML = "<li>هنوز دامنه‌ای پاک یافته نشده است.</li>";
    }
    updateDownloadBtnState();

    if (!data.running) {
      clearInterval(autoScanInterval);
      autoBtn.disabled = false;
      cancelBtn.disabled = true;
      showProgress(100);

      autoStatus.textContent = data.cancel
        ? `وضعیت: اسکن اتوماتیک لغو شد - دامنه‌های پاک: ${data.results_count}`
        : `وضعیت: اسکن اتوماتیک پایان یافت - دامنه‌های پاک: ${data.results_count}`;
    }
  } catch (e) {
    clearInterval(autoScanInterval);
    alert("خطا در دریافت وضعیت اسکن: " + e.message);
    autoStatus.textContent = "وضعیت: خطا در دریافت وضعیت اسکن";
    autoBtn.disabled = false;
    cancelBtn.disabled = true;
    resetProgress();
  }
}

async function cancelAutoScan() {
  cancelBtn.disabled = true;
  try {
    await fetch(`${BASE_URL}/clean-items/auto/cancel?type=reality`, { method: "POST" });
    resetProgress();
  } catch (e) {
    alert("خطا در لغو اسکن: " + e.message);
  }
}

async function manualScan() {
  const input = manualInput.value.trim();
  if (!input) {
    alert("لطفاً حداقل یک دامنه وارد کنید.");
    return;
  }
  const domains = input.split("\n").map(d => d.trim()).filter(Boolean);
  domainList.innerHTML = "<li>در حال بررسی...</li>";
  manualBtn.disabled = true;

  try {
    const res = await fetch("http://localhost:8000/clean-items/manual/check?type=reality", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items: domains }),  // اینجا items
    });
    if (!res.ok) throw new Error("درخواست اسکن دستی ناموفق بود");
    const data = await res.json();

    domainList.innerHTML = "";
    if (data.results && data.results.length > 0) {  // اینجا results
      data.results.forEach(domain => {
        const li = document.createElement("li");
        li.textContent = domain;
        domainList.appendChild(li);
      });
    } else {
      domainList.innerHTML = "<li>هیچ دامنه پاکی یافت نشد.</li>";
    }
    updateDownloadBtnState();
  } catch (e) {
    alert("خطا در اسکن دستی دامنه‌ها: " + e.message);
  } finally {
    manualBtn.disabled = false;
  }
}


// --- IPها ---

async function startIPAutoScan() {
  const provider = ipTypeSelect.value;
  const ipCountInput = document.getElementById("ip-count-input");
  const useTLSCheckbox = document.getElementById("use-tls-check");  // 👈 اضافه شد

  let requiredCount = parseInt(ipCountInput?.value);
  if (isNaN(requiredCount) || requiredCount <= 0) requiredCount = 2;

  const useTLSCheck = useTLSCheckbox?.checked ? "true" : "false";  // 👈 مقدار واقعی

  autoStatus.style.display = "none";
  ipStatus.style.display = "block";

  ipStatus.textContent = "در حال اسکن IPهای " + provider;
  ipAutoBtn.disabled = true;
  ipCancelBtn.disabled = false;
  ipList.innerHTML = "<li>در حال دریافت و بررسی IPها...</li>";
  showProgress(0);

  try {
    // ارسال پارامتر تعداد IP تمیز مورد نیاز به API (مثلا به صورت کوئری‌استرینگ)
    const res = await fetch(
      `${BASE_URL}/clean-items/auto/start?type=${provider}&required_count=${requiredCount}&use_tls_check=${useTLSCheck}`
    );  // 👈 استفاده از مقدار درست
    const data = await res.json();
    if (data.status === "started") {
      ipScanInterval = setInterval(() => fetchIPAutoProgress(provider), 2000);
    } else {
      throw new Error("اسکن قبلاً در حال انجام است");
    }
  } catch (e) {
    alert("خطا در شروع اسکن IP: " + e.message);
    resetProgress();
    ipAutoBtn.disabled = false;
    ipCancelBtn.disabled = true;
  }
}


async function fetchIPAutoProgress(provider) {
  try {
    const res = await fetch(`${BASE_URL}/clean-items/auto/progress?type=${provider}`);
    const data = await res.json();

    let percent = 0;
    if (data.total && data.total > 0) {
      percent = Math.min(100, Math.round((data.done / data.total) * 100));
    }

    showProgress(percent);

    const providerLabel = provider === "fastly" ? "فستلی" : provider === "cloudflare" ? "کلودفلر" : "نامشخص";
    ipStatus.textContent = `وضعیت: ${data.running ? "در حال اسکن" : "پایان یافته"} - IPهای پاک ${providerLabel}: ${data.results_count} از ${data.total}`;

    ipList.innerHTML = "";
    if (data.results?.length > 0) {
      data.results.forEach(ip => {
        const li = document.createElement("li");
        li.textContent = ip;
        ipList.appendChild(li);
      });
    } else {
      ipList.innerHTML = "<li>هنوز IP پاک یافته نشده است .</li>";
    }
    updateDownloadBtnState();

    if (!data.running) {
      clearInterval(ipScanInterval);
      ipAutoBtn.disabled = false;
      ipCancelBtn.disabled = true;
      showProgress(100);
    }
  } catch (e) {
    alert("خطا در دریافت وضعیت IP: " + e.message);
    clearInterval(ipScanInterval);
    resetProgress();
  }
}


async function cancelIPScan() {
  ipCancelBtn.disabled = true;
  const provider = ipTypeSelect.value;
  try {
    await fetch(`${BASE_URL}/clean-items/auto/cancel?type=${provider}`, { method: "POST" });
  } catch (e) {
    alert("خطا در لغو اسکن IP: " + e.message);
  }
}

async function manualIPScan() {
  const input = ipManualInput.value.trim();
  const useTLSCheckbox = document.getElementById("use-tls-check");

  if (!input) return alert("لطفاً IP وارد کنید");

  const ips = input.split("\n").map(d => d.trim()).filter(Boolean);
  ipList.innerHTML = "<li>در حال بررسی IPها...</li>";
  ipManualBtn.disabled = true;

  const useTLSCheck = useTLSCheckbox?.checked === true; // ✅ به‌جای رشته، مقدار بولی واقعی
  const provider = ipTypeSelect.value;

  try {
    const url = `${BASE_URL}/clean-items/manual/check?type=${provider}&use_tls_check=${useTLSCheck}`;
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items: ips, use_tls_check: useTLSCheck }), // ✅ اینجا هست
    });

    if (!res.ok) throw new Error("درخواست اسکن دستی ناموفق بود");

    const data = await res.json();

    ipList.innerHTML = "";
    if (data.results?.length > 0) {
      data.results.forEach(ip => {
        const li = document.createElement("li");
        li.textContent = ip;
        ipList.appendChild(li);
      });
    } else {
      ipList.innerHTML = "<li>هنوز IP پاک یافته نشده است .</li>";
    }

    updateDownloadBtnState();
  } catch (e) {
    alert("خطا در اسکن دستی IP: " + e.message);
  } finally {
    ipManualBtn.disabled = false;
  }
}

// --- ابزارهای مشترک ---

function showProgress(percent) {
  progressContainer.style.display = "block";
  progressPercent.style.display = "block";
  progressBar.style.width = percent + "%";
  progressPercent.textContent = percent + "%";
}

function resetProgress() {
  clearInterval(autoScanInterval);
  clearInterval(ipScanInterval);
  progressBar.style.width = "0%";
  progressContainer.style.display = "none";
  progressPercent.style.display = "none";
}


function updateDownloadBtnState() {
  const domainItems = domainList.querySelectorAll("li");
  const ipItems = ipList.querySelectorAll("li");

  const hasValidDomains = Array.from(domainItems).some(li => {
    const text = li.textContent.trim();
    return text !== "" &&
           text !== "نتایج دامنه‌ها در اینجا نمایش داده می‌شود" &&
           !text.includes("یافت نشد") &&
           !text.includes("در حال اسکن دامنه‌ها") &&
           !text.includes("در حال بررسی") &&
           !text.includes("هنوز دامنه‌ای پاک یافته نشده است.");
  });

  const hasValidIPs = Array.from(ipItems).some(li => {
    const text = li.textContent.trim();
    return text !== "" &&
           text !== "نتایج IPها در اینجا نمایش داده می‌شود" &&
           !text.includes("یافت نشد") &&
           !text.includes("در حال دریافت و بررسی IPها") &&
           !text.includes("در حال بررسی IPها") &&
           !text.includes("هنوز IP پاک یافته نشده است .");
  });

  downloadBtn.disabled = !hasValidDomains;
  downloadIPsBtn.disabled = !hasValidIPs;
}



function downloadList(listElement, filename) {
  const items = Array.from(listElement.querySelectorAll("li"))
    .map(li => li.textContent)
    .filter(Boolean);

  const blob = new Blob([items.join("\n")], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}


// رویدادها
downloadBtn.addEventListener("click", () => downloadList(domainList, "clean_domains.txt"));
downloadIPsBtn.addEventListener("click", () => downloadList(ipList, "clean_ips.txt"));

autoBtn.addEventListener("click", startAutoScan);
cancelBtn.addEventListener("click", cancelAutoScan);
manualBtn.addEventListener("click", manualScan);

if (ipAutoBtn) ipAutoBtn.addEventListener("click", startIPAutoScan);
if (ipCancelBtn) ipCancelBtn.addEventListener("click", cancelIPScan);
if (ipManualBtn) ipManualBtn.addEventListener("click", manualIPScan);
