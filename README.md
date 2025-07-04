# 🛡️ Mapsim Scanner Utility

An advanced tool to **scan and identify clean, filtering-compatible domains and IP addresses** for use with **Reality** and major CDN providers such as **Fastly** and **Cloudflare**.

This utility helps detect clean internet resources unaffected by filtering (e.g., in Iran), offering a powerful **REST API** with a **modern, responsive web UI**.

---

## 🚀 Features

- 🔍 **Automatic & manual scanning** of domains and IPs from user input or public sources
- 🌐 **Domain validation** via port 443 (HTTPS), TLS handshake, and certificate inspection
- 📡 **IP verification** including:
  - Ping and TCP port 443 check
  - WHOIS lookup to verify CDN ownership
  - TLS SNI handshake to ensure compatibility
- 📥 **CIDR support & dynamic IP sources** via JSON and live APIs
- 🖥️ **FastAPI backend** with live RESTful endpoints
- 📊 **Real-time progress reporting** and cancellation support
- 🧪 Designed for regional testing (e.g., filtering in Iran)
- 💡 Easily extendable to support more CDNs or custom sources

---

## 🧰 Prerequisites


- Python 3.9 or higher
- `pip` (Python package manager)
- (Optional) Node.js & npm — for frontend development or bundling assets
- Internet access — for domain/IP testing and retrieving external sources

---

## 📦 Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/MAPSIM-co/Mapsim_Scanner_Utility.git
cd Mapsim_Scanner_Utility
```

### 2. Create and activate a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate
```

-  For Windows
  
```bash
venv\Scripts\activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt

```
### 4. Run the FastAPI server

```bash
uvicorn backend.main:app --reload
```

-  🌐 You can open the UI in your browser via:  
  `http://localhost:<your-port>/index.html`  

-  ℹ️ Make sure to read the **Web Server** section for details on running a local server.

    
-   The ```server runs``` by default at http://localhost:8000
  
-   API ```docs``` available at http://localhost:8000/docs

### 5. Run the frontend UI

  Open ```frontend/index.html``` in your web browser
  If you change the API server address, update the BASE_URL variable in ```frontend/app.js``` accordingly

---

## 🌐 Frontend Web Server Setup
    
  To run the frontend UI correctly, **you must serve the frontend folder using a web server.** 
  Do NOT open ```index.html``` directly from your file system ```(file://)``` — it will break due to CORS restrictions.

### 🔧 Option 1: Python built-in server

```bash
cd frontend
python3 -m http.server 8080
```

Open in browser:
```bash
http://localhost:8080/index.html
```

### 🔧 Option 2: Node.js http-server

```bash
npm install -g http-server
cd frontend
http-server -p 8080
```
Open in browser:
```bash
http://localhost:8080/index.html
```
💡 If you change API address, update BASE_URL in ```frontend/app.js```

## 💻 Windows Instructions

Open ```Command Prompt``` (CMD)
Navigate to the frontend folder:

```bash
cd path\to\Mapsim_Scanner_Utility\frontend
```
Run:
```bash
python -m http.server 8080
```
Open:
```bash
http://localhost:8080/index.html
```

## Software (Option) :

### 🌐 Free Local Web Server Tools

To serve the ```frontend/index.html``` on ```bash
http://localhost:<your-port>``` , you can use any of the following free web servers depending on your operating system:

### 🪟 Windows

| Tool         | Description |
|--------------|-------------|
| **XAMPP**    | All-in-one Apache + PHP + MySQL stack. Easy to install and use. [🔗](https://www.apachefriends.org/index.html) |
| **WampServer** | Apache + PHP + MySQL for Windows only. Simple UI. [🔗](https://www.wampserver.com/en/) |
| **Laragon**  | Modern and lightweight web server with support for Apache/Nginx. [🔗](https://laragon.org/) |
| **Python HTTP Server** | Built-in in Python. For static files only: `python -m http.server` |
| **Node.js http-server** | Install via npm: `npm install -g http-server`, then run `http-server ./frontend` |

### 🍎 macOS

| Tool                  | Description                                                                                      |
|-----------------------|--------------------------------------------------------------------------------------------------|
| **MAMP**              | macOS alternative to XAMPP. Includes Apache, PHP, MySQL. [🔗](https://www.mamp.info/en/)         |
| **Python HTTP Server**| Comes with macOS. Run in terminal: `python3 -m http.server`                                      |
| **Node.js http-server**| Static server with Node.js: Install via `npm install -g http-server` and run in folder          |
| **Caddy**             | Modern CLI web server with auto HTTPS (optional). [🔗](https://caddyserver.com/)                 |
| **Nginx (via Homebrew)**| Install with: `brew install nginx`, then configure `/usr/local/etc/nginx/nginx.conf` for local serving |


### 🐧 Linux (Ubuntu, Debian, Arch, etc.)

| Tool                 | Description                                                                                      |
|----------------------|--------------------------------------------------------------------------------------------------|
| **Apache2**           | Full-featured HTTP server. Install with: `sudo apt install apache2`                             |
| **Nginx**             | Lightweight and efficient. Install with: `sudo apt install nginx`                               |
| **Python HTTP Server**| Quickest for static content. Run in terminal: `python3 -m http.server`                          |
| **Node.js http-server**| Simple static server. Install via `npm install -g http-server`                                  |
| **Caddy**             | Easy to configure and powerful with HTTPS. [🔗](https://caddyserver.com/)                        |

---

### ✅ Recommended for This Project
For most users, simply open a terminal in the ```frontend/``` folder and run:
```bash
python3 -m http.server
```
Then open 

`http://localhost:<your-port>/index.html`  

in your browser.

---

## 🧱 Project Structure

```graphql
Mapsim Scanner Utility/
├── backend/                            # FastAPI backend logic and scanning modules
│   ├── __init__.py                     # Marks this directory as a Python package
│   ├── main.py                         # FastAPI app instance and route definitions
│   ├── utils.py                        # Core logic for domain/IP scanning and validation
│   ├── sources.py                      # Management of domain/IP sources and static ranges
│   └── data/                           # Data directory for domain/IP source lists
│       ├── domain_sources.json         # JSON list of Reality-compatible domain source URLs
│       ├── ip_sources.json             # JSON list of IP source URLs (e.g., from Fastly API)
│       ├── fastly_ranges.json          # Static IP ranges (CIDR blocks) for Fastly
│       └── cloudflare_ranges.json      # Static IP ranges (CIDR blocks) for Cloudflare
│
├── frontend/                           # Static frontend files for browser UI
│   ├── index.html                      # Main user interface with layout and inputs
│   ├── app.js                          # JavaScript logic for interacting with API and UI updates
│   └── style.css                       # Basic styling for the web interface
│
├── requirements.txt                    # Python package dependencies for backend
├── README.md                           # Project description, usage, and documentation
└── .gitignore                          # Git ignore rules (e.g. for __pycache__, .env files, etc.)
```

---

### 🛠️ Usage

## ▶️ Auto Scan (Domains)

  - Click **"Start Auto Scan Domains"**
  - View progress and clean domains found
  - Cancel anytime with the Cancel button

## ✍️ Manual Scan (Domains)

  - Enter domain names line-by-line
  - Click **Manual Scan**
  - Results show valid domains usable with Reality

## ⚡ Auto Scan (IPs)

  - Select provider: ```Fastly``` or ```Cloudflare```
  - Set required count of clean IPs
  - Toggle ```TLS``` check if needed
  - Click **Start**, monitor results live

## 🧪 Manual Scan (IPs)

  - Paste IP addresses line-by-line
  - Toggle ```TLS``` check
  - Click **Manual IP Scan**

## 📄 Download Results

Use the download buttons to get clean domains/IPs as ```.txt``` files

## ⚠️ Notes & Tips

  - For **accurate filtering test**, use an IP located **inside Iran**
  - Keep ```domain_sources.json``` and ```ip_sources.json``` up to date
  - For better accuracy, ensure:
  - ```DNS``` is not hijacked
  - **Connections aren’t intercepted by proxies or filters**
  - You can add your own CDN ranges or source URLs in the ```data/``` directory


## 🤝 Contributing

Contributions are welcome!

  - 🆕 Add support for more ```CDN``` providers
  - 🧠 Improve scanning logic or heuristics
  - 🎨 Enhance the frontend design
  - 🐞 Report bugs via GitHub [Issues](https://github.com/MAPSIM-co/Mapsim_Scanner_Utility/issues)
  - Please submit pull requests with clear changes and documentation.

## 📜 License

This project is licensed under the MIT License — feel free to use and modify with attribution

## 📬 Contact
For support, questions, or collaboration:

  - GitHub [Issues](https://github.com/MAPSIM-co/Mapsim_Scanner_Utility/issues)
  - Telegram : ([Support Telegram](https://telegram.me/Tarantula_trade_chBot?start=5580469558))
    
 ---
