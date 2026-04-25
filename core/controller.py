"""Controlador principal de FileMaster."""
from __future__ import annotations

import json
import logging
import threading
import time
import uuid
import re
import unicodedata
from difflib import SequenceMatcher
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from ai.hint_classifier import classify_by_hints, get_multi_categories
from ai.classifier import DocumentClassifier
from ai.clustering import DocumentClusterer
from ai.embeddings import EmbeddingService, centroid
from ai.keyword_extractor import KeywordExtractor
from ai.neural_classifier import NeuralCategoryClassifier
from ai.text_utils import title_from_keywords, generate_category_name
from config.settings import (
    DEFAULT_DUPLICATES_FOLDER_NAME,
    HISTORY_DB_PATH,
    UserConfig,
    ensure_data_files,
    load_categories,
    load_runtime_state,
    load_user_config,
    save_categories,
    save_runtime_state,
    save_user_config,
)
from core.duplicate_detector import DuplicateDetector
from core.file_manager import FileManager
from core.history import HistoryRecord, HistoryRepository
from core.models import CategoryProfile, CycleSummary, DocumentRecord, DuplicateGroup, GroupProposal
from core.organizer import Organizer
from core.text_extractor import TextExtractor
from core.watcher import FileWatcher


# Categorías especializadas tienen prioridad sobre genéricas
# Orden: más específica primero
CATEGORY_PRIORITY = {
    "Hacking Etico": 1,
    "Ciberseguridad": 2,
    "Inteligencia Artificial": 3,
    "Base de Datos": 4,
    "Administracion de Redes": 5,
    "Desarrollo Web": 6,
    "Desarrollo Movil": 7,
    "Tecnologias de Virtualizacion": 8,
    "Tecnologias en la Nube": 9,
    "Taller de Investigacion": 10,
    "Programacion Logica y Funcional": 11,
    "Desarrollo de Software": 12,
    "Arquitectura de Computadoras": 13,
    "Sistemas Operativos": 14,
    "Matematicas Discretas": 15,
    "Estadistica": 16,
    "Ciencia de Datos": 17,
}

KNOWN_CATEGORY_HINTS = {
    "Inteligencia Artificial": {
        "ia", "ai", "inteligenciaartificial", "machine", "learning", "ml", "redneuronal",
        "algoritmo", "clasificacion", "regresion", "clustering", "aprendizaje",
        "entrenamiento", "modelo", "prediccion", "embedding", "embeddings",
        "transformer", "nlp", "deeplearning", "dl", "backpropagation",
        "tensorflow", "pytorch", "keras", "perceptron", "overfitting", "underfitting",
        "neuralnetwork", "cnn", "rnn", "lstm", "gru", "dataset", "dataloader",
        "train", "test", "validation", "accuracy", "loss", "optimizer",
        "precision", "recall", "f1score", "auc", "roc", "confusion", "metric",
        "regresionlineal", "regresionlogistica", "clasificador", "supervisado", "no-supervisado",
        "kmeans", "knn", "svm", "randomforest", "xgboost", "gradientboosting",
        "generativo", "discriminativo", "bayes", "naive", "decisiontree", "arbol",
        "optimizacion", "gradiente", "descenso", "adam", "sgd", "rmsprop",
        "token", "tokenizer", "word2vec", "bert", "gpt", "llm", "langchain",
        "rag", "prompt", "fine-tuning", "transferlearning", "huggingface",
        "yolo", "objectdetection", "segmentation", "vision", "computer",
        "reinforcement", "qlearning", "dqn", "policy", "reward", "environment",
        "autoencoder", "vae", "gan", "diffusion", "stable", "midjourney"
    },
    "Base de Datos": {
        "sqldatabase", "mysql", "postgresql", "postgres", "oracle", "mariadb", "db",
        "sql", "query", "joins", "normalizacion", "normalforms", "relacional",
        "mongodb", "redis", "sqlite", "nosql", "database", "databases",
        "mysqlworkbench", "phpmyadmin", "dbeaver", "sequelpro", "datagrip",
        "tabla", "fila", "columna", "registro", "tupla", "campo", "indice", "index",
        "primarykey", "foreignkey", "primary", "secondary", "unique", "check", "constraint",
        "cursor", "transaccion", "commit", "rollback", "savepoint",
        "storedprocedure", "storedfunction", "procedure", "function", "trigger",
        "view", "views", "materialized", "routine", "udf",
        "select", "insert", "update", "delete", "create", "alter", "drop",
        "where", "groupby", "having", "orderby", "order", "limit", "offset",
        "inner", "left", "right", "outer", "cross", "full", "natural", "self",
        "er", "modeloer", "diagramaer", "cardinalidad", "participacion",
        "ddl", "dml", "dcl", "tcl", "backup", "restore", "replication",
        "partitioning", "sharding", "clustering", "ha", "failover", "rac",
        "connectionpool", "pool", "isolation", "lock", "deadlock", "transaction"
    },
    "Administracion de Redes": {
        "redes", "redesdecomputadoras", "redesdearea", "lan", "man", "wan",
        "router", "switch", "hub", "bridge", "modem", "protocolo",
        "tcpip", "tcp", "udp", "icmp", "ipv4", "ipv6", "ip",
        "subred", "subnet", "vlan", "vlanid", "ospf", "bgp", "eigrp", "rip",
        "dns", "dhcp", "nat", "pat", "抽", "gateway", "default",
        "cisco", "ccna", "ccnp", "ccie", "packettracer", "gns3", "ciscoios",
        "ethernet", "wifi", "wlan", "inalambrico", "wireless", "accesspoint",
        "snmp", "nms", "zabbix", "nagios", "monitor", "monitoring", "prometheus",
        "traceroute", "tracert", "ping", "netstat", "ipconfig", "ifconfig", "nslookup",
        "dig", "host", "arp", "mac", "dnssec", "ddns",
        "firewall", "acl", "vty", "console", "telnet", "ssh", "rdp",
        "vpn", "ipsec", "tunnel", "gre", "mpls", "openvpn", "wireguard",
        "topologia", "anillo", "estrella", "bus", "malla", "hibrida",
        " bandwidth", "latency", "jitter", "packetloss", "throughput", "qos",
        "loadbalancer", "balanceador", "cdn", "cache", "proxy", "reverse",
        "multicast", "broadcast", "unicast", "anycast", "IGMP", "ARP"
    },
    "Hacking Etico": {
        "pentest", "penetration", "testing", "pentesting", "vulnerabilidad", "vuln",
        "exploit", "cve", "cwe", "owasp", "nist", "iso27001",
        "nmap", "zenmap", "escaneo", "scan", "puertos", "portscan", "fingerprinting",
        "metasploit", "msfconsole", "msfvenom", "meterpreter", "armitage",
        "kali", "linux", "backbox", "parrot", "blackarch", "whonix",
        "burp", "owaspzap", "sqlmap", "nikto", "gobuster", "dirb",
        "hydra", "john", "hashcat", "cracking", "password", "credential",
        "reverse", "shell", "bind", "payload", "msf",
        "buffer", "overflow", "formatstring", "integer", "racecondition",
        "xss", "csrf", "sqli", "rce", "lfi", "rfi", "xxe", "ssrf",
        "infogathering", "recon", "footprinting", "osint",
        "enumeration", "privilege", "escalation", "privesc",
        "persistence", "pivoting", "covering", "tracks", "forensics",
        "malware", "ransomware", "trojan", "virus", "worm", "spyware",
        "phishing", "spearphishing", "whaling", "socialengineering",
        "WAF", "IDS", "IPS", "SIEM", "SOC", "log", "logging"
    },
    "Tecnologias de Virtualizacion": {
        "virtualizacion", "virtualization", "vmware", "virtualbox", "hyperv", "qemu", "kvm",
        "hypervisor", "type1", "type2", "baremetal", "hosted",
        "contenedor", "container", "docker", "kubernetes", "k8s", "openshift",
        "containerd", "podman", "CRI-O", "containerruntime",
        "dockerfile", "dockercompose", "docker-compose", "helmchart", "helm",
        "imagenvm", "snapshot", "snapshotting", "clon", "clone", "template",
        "esxi", "vcenter", "vsphere", "vrealize", "vcloud", "vcac",
        "proxmox", "pve", "ceph", "glusterfs", "cinder", "swift",
        "vagrant", "packer", "terraform", "ansible", "cloudinit",
        "iso", "ovf", "ova", "vmdk", "qcow2", "vdi", "img",
        "bridged", "bridging", "nat", "hostonly", "host-only", "internal", "redinterna"
    },
    "Tecnologias en la Nube": {
        "nube", "cloud", "cloudcomputing", "iaas", "paas", "saas", "faas", "baas",
        "aws", "amazon", "azure", "googlecloud", "gcp", "digitalocean", "linode",
        "ec2", "s3", "lambda", "ecs", "eks", "rds", "dynamodb", "cloudfront",
        "azurevm", "azurefunctions", "aks", "aks", "azureadb", "keyvault", "cosmosdb",
        "gcpcompute", "gcpfunctions", "gke", "gcpstorage", "bigquery", "cloudstorage",
        "serverless", "functions", "functionas", "microservices", "microservicio",
        "iam", "identity", "role", "policy", "secret", "key", "token", "oauth",
        "bucket", "storage", "blob", "cdn", "cloudfront", "elb", "alb", "nlb",
        "terraform", "cloudformation", "cdk", "sam", "serverless",
        "cicd", "pipeline", "codebuild", "codedeploy", "codepipeline", "githubactions",
        "cloudwatch", "logs", "metrics", "monitoring", "sns", "sqs", "kinesis",
        "grafana", "prometheus", "datadog", "newrelic", "logsinsights",
        "vpc", "subnet", "route53", "cloudfront", "apigateway", "loadbalancer",
"efs", "fsx", "storagegateway", "glacier", "s3glacier"
    },
    "Taller de Investigacion": {
        "investigacion", "investigacionde", "research", "investigative",
        "metodologia", "metodologico", "methodology", "method",
        "hipotesis", "hypothesis", "objetivo", "objective", "goal", "problema", "problem",
        "justificacion", "justification", "rationale",
        "marco", "teorico", "conceptual", "legal", "framework",
        "bibliografia", "referencia", "bibliography", "reference",
        "cita", "quotation", "apa", "normas apa", "citation",
        "resumen", "abstract", "summary", "introduccion", "introduction",
        "resultado", "resultados", "results", "conclusion", "conclusions",
        "recomendacion", "recommendation", "suggestion",
        "tesis", "tesina", "monografia", "thesis", "dissertation",
        "encuesta", "questionnaire", "survey", "entrevista", "interview", "observation",
        "cuestionario", "instrument", "instruments", "muestra", "sample", "sampling",
        "cuantitativo", "quantitative", "cualitativo", "qualitative", "mixto", "mixed", "method",
        "proyecto", "project", "informe", "report", "reporte", "deliverable",
        "documento", "document", "articulo", "article", "paper", "publication",
        "googleacademico", "scholar", "researchgate", "academia", "arxiv",
        "moodle", "lms", "canvas", "blackboard", "aula", "classroom", "campusvirtual",
        "variable", "dependent", "independent", "correlation", "causality",
        "poblacion", "population", "muestral", "sampling", "confianza",
        "significancia", "significance", "alpha", "beta", "p-value"
    },
    "Programacion Logica y Funcional": {
        "prolog", "haskell", "lisp", "scheme", "erlang", "elixir", "clojure", "F#",
        "funcional", "functional", "logica", "logical", "logicprogramming",
        "predicado", "predicate", "clausula", "clause", "fact", "rule",
        "recursion", "recursive", "tail", "tailcall", "accumulator",
        "lambda", "closure", "curry", "currying", "partial", "application",
        "matching", "pattern", "unification", "backtracking", "OccursCheck",
        "inmutable", "immutable", "inmutability", "pure", "purity", "sideeffect",
        "lazy", "evaluation", "eager", "monad", "functor", "applicative",
        "inferencia", "inference", "type", "polymorphic", "generic",
        "declarativo", "declarative", "declarativeprogramming",
        "higherorder", "firstclass", "combinator", "composition",
        "tree", "list", "algebraic", "adt", "sumtype", "producttype"
    },
    "Desarrollo Web": {
        "html", "html5", "html", "css", "css3", "sass", "scss", "less",
        "javascript", "js", "typescript", "ts", "ecmascript",
        "react", "reactjs", "angular", "angularjs", "vue", "vuejs", "svelte",
        "frontend", "front-end", "backend", "back-end", "fullstack", "full-stack",
        "api", "apis", "rest", "restful", "graphql", "gql",
        "http", "https", "http2", "http3", "request", "response",
        "bootstrap", "tailwind", "bulma", "material", "responsive", "adaptive", "mobilefirst",
        "dom", "bom", "ajax", "fetch", "axios", "json", "xml", "html",
        "web", "website", "sitio", "page", "navegador", "browser", "chrome", "firefox",
        "servidor", "server", "hosting", "dominio", "domain", "dns", "ssl", "tls", "https",
        "cookie", "session", "localstorage", "cors", "csrf", "xss",
        "webpack", "vite", "rollup", "parcel", "esbuild", "babel", "postcss",
        "pwa", "progressive", "webapp", "manifest", "serviceworker"
    },
    "Desarrollo Movil": {
        "html", "css", "javascript", "react", "angular", "vue",
        "frontend", "backend", "fullstack", "api", "rest", "graphql",
        "http", "css", "bootstrap", "tailwind", "responsive", "dom",
        "ajax", "json", "xml", "web", "navegador", "servidor", "hosting", "dominio"
    },
    "Desarrollo Movil": {
        "android", "androidstudio", "ios", "swift", "objectivec",
        "flutter", "dart", "reactnative", "xamarin", "kotlin", "jetpack",
        "mobile", "app", "aplicacion", "aplicativo", "celular", "tablet", "smartphone",
        "gradle", "maven", "cocoapods", "sdk", "ndk", "api", "apis",
        "playstore", "googleplay", "appstore", "appstoreconnect", "fdroid",
        "ui", "ux", "ui design", "materialdesign", "material",
        "activity", "fragment", "intent", "broadcast", "service",
        "view", "viewmodel", "livedata", "navigation", "room", "sqlite",
        "constraintlayout", "linearlayout", "relativelayout", "recyclerview",
        "coroutines", "async", "thread", "background", "foreground"
    },
    "Desarrollo de Software": {
        "software", "development", "developer", "programacion", "programming",
        "agile", "agile", "scrum", "kanban", "sprint", "standup",
        "uml", "diagram", "use", "case", "sequence", "class", "activity",
        "requirement", "requerimiento", "specification", "spec", "Functional", "NonFunctional",
        "testing", "test", "unittest", "integration", "e2e", "automation",
        "tdd", "bdd", "testdriven", "behaviordriven",
        "refactoring", "code", "smell", "technicaldebt",
        "designpatterns", "singleton", "factory", "observer", "strategy", "decorator",
        "solid", "principles", "solidprinciples", "clean", "cleancode",
        "versioncontrol", "git", "github", "gitlab", "bitbucket", "svn",
        "branch", "merge", "pull", "push", "commit", "revert", "cherrypick",
        "code review", "review", "pr", "mr", "cr", "approval"
    },
    "Ciberseguridad": {
        "seguridad", "ciberseguridad", "cybersecurity", "infosec", "security",
        "criptografia", "cryptography", "encryption", "encriptacion", "decryption",
        "cipher", "aes", "rsa", "sha", "md5", "hash", "hashing", "salt",
        "firewall", "fw", "waf", "ips", "ids", "idss", "siem", "soc", "xdr",
        "autenticacion", "authentication", "auth", "authorization", "oauth", "oauth2", "saml", "sso",
        "ldap", "active directory", "ad", "kerberos", "ntlm", "basic", "digest",
        "malware", "malicious", "virus", "worm", "trojan", "ransomware", "spyware", "adware",
        "phishing", "spearphishing", "vishing", "smishing", "whaling", "socialengineering",
        "apt", "threat", "attacker", "attck", "mitre", "framework",
        "zero-day", "exploit", "vulnerability", "cve", "cwe", "owasp",
        "incident", "response", "forensics", "malwareanalysis", "reverseengineering",
        "penetration", "assessment", "audit", "vulnerabilityassessment",
        "hardening", "patch", "update", "vulnerabilitymanagement"
    },
    "Ciencia de Datos": {
        "data", "datos", "analytics", "analitica", "dataanalytics", "dataanalysis",
        "bigdata", "big data", "hadoop", "spark", "databricks", "flink",
        "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
        "visualization", "visualizacion", "dashboard", "tableau", "powerbi", "looker",
        "etl", "elt", "pipeline", "datapipeline", "airflow", "luigi",
        "datawarehouse", "dw", "datalake", "warehouse", "lakehouse",
        "statistics", "estadistica", "descriptive", "inferential", "probability",
        "hypothesis", "testing", "significance", "pvalue", "confidence",
        "regression", "correlation", "anova", "chi-square", "t-test",
        "machinelearning", "ml", "supervised", "unsupervised", "semi",
        "neural", "deep", "reinforcement", "recommendation", "collaborative",
        "feature", "engineering", "selection", "extraction", "scaling", "encoding",
        "confusionmatrix", "accuracy", "precision", "recall", "f1", "auc", "roc",
        "eda", "exploratory", "analysis", "preprocessing", "cleaning", "wrangling",
        "python", "r", "scala", "julia", "sql", "nosql"
    },
    "Arquitectura de Computadoras": {
        "arquitectura", "architecture", "computer", "computers", "cpu", "procesador",
        "gpu", "graphics", "nvidia", "amd", "intel", "ram", "memoria", "memory",
        "storage", "almacenamiento", "ssd", "hdd", "disk", " disco",
        "assembly", "ensamblador", "assembler", "masm", "nasm", "gas",
        "instruction", "instructionset", "isa", "opcode", "operand", "register",
        "registers", "pc", "sp", "bp", "si", "di", "ax", "bx", "cx", "dx",
        " interrupt", " irq", "dma", "paging", "segmentation", "virtualmemory",
        "cache", "l1", "l2", "l3", "Associative", "tlb", "mmu",
        "bus", "address", "data", "controlbus", "systembus", "frontside",
        "pipeline", "hazard", "stall", "bubble", "branchprediction",
        " alu", "cu", "cu", "寄存器", "decoder", "encoder", "multiplexer"
    },
    "Sistemas Operativos": {
        "so", "os", "operativo", "operative", "operative",
        "windows", "win", "windows10", "windows11", "winserver",
        "linux", "ubuntu", "debian", "fedora", "centos", "redhat", "arch",
        "macos", "apple", "ios", "darwin", "unix", "freebsd", "openbsd",
        "kernel", " kernel", "shell", "bash", "zsh", "fish", "terminal", "console",
        "process", "proceso", "thread", "hilo", "scheduling", "scheduler",
        "memory", "virtual", "paging", "swapping", "allocation",
        "file", "filesystem", "fs", "ntfs", "ext4", "btrfs", "apfs",
        "device", "driver", "device driver", "kernel module",
        "systemcall", "syscall", "api", "interrupt", "exception", "trap",
        "multitasking", "multiprogramming", "timesharing", "real-time",
        "concurrency", "parallelism", "deadlock", "starvation", "priorityinversion"
    },
    "Matematicas Discretas": {
        "discreta", "discrete", "mathematics", "logica", "logic", "set", "conjunto",
        "relation", "relacion", "function", "funcion", "mapping",
        "graph", "grafo", "vertex", "vertice", "edge", "arista", "node",
        "path", "camino", "cycle", "ciclo", "path", "circuit",
        "tree", "arbol", "root", "leaf", "branch", "subtree",
        "directed", "undirected", "weighted", "unweighted",
        "bfs", "dfs", "dijkstra", "bellman", "floyd", "prim", "kruskal",
        "topological", "ordering", "sorting", "dag", "network", "flow",
        "combinatorics", "combination", "permutation", "principle", "inclusion", "pigeonhole",
        "recurrence", "recursion", "induction", "proof", "theorem", "lemma",
        "boolean", "algebra", "gate", "circuit", "truth", "table",
        "modular", "arithmetic", "congruence", "gcd", "lcm", "prime"
    },
    "Estadistica": {
        "estadistica", "statistics", "statistic", "descriptive", "inferential",
        "mean", "media", "median", "moda", "mode", "variance", "varianza",
        "deviation", "desviacion", "standard", "standarddeviation",
        "distribution", "distribucion", "normal", "gaussian", "binomial", "poisson", "exponential",
        "probability", "probabilidad", "random", "aleatorio", "stochastic",
        "sample", "muestra", "population", "poblacion", "sampling", "muestreo",
        "hypothesis", "testing", "test", "prueba", "significance", "significancia",
        "p-value", "alpha", "beta", "confidence", "interval", "confidenceinterval",
        "correlation", "correlation", "regression", "regresion",
        "anova", "manova", "t-test", "chisquare", "kolmogorov", "smirnov",
        "bayesian", "bayes", "prior", "posterior", "likelihood",
        "estimator", "estimador", "bias", "unbiased", "efficient"
    },
}

logger = logging.getLogger(__name__)

LEARNING_KEYWORDS_LIMIT = 60
LEARNING_MIN_TOKEN_LEN = 4
LEARNING_CONFIDENCE_THRESHOLD = 0.82
NEURAL_MIN_COVER_CONFIDENCE = 0.82
NEURAL_MIN_CONTENT_CONFIDENCE = 0.76


class FileMasterController:
    def __init__(self, notify_callback=None) -> None:
        ensure_data_files()
        self.notify_callback = notify_callback
        self.config = load_user_config()
        self.file_manager = FileManager()
        self.text_extractor = TextExtractor()
        self.embedder = EmbeddingService()
        self.keyword_extractor = KeywordExtractor()
        self.neural_classifier = NeuralCategoryClassifier()
        self.neural_classifier.pre_train()
        self.clusterer = DocumentClusterer()
        self.classifier = DocumentClassifier()
        self.duplicate_detector = DuplicateDetector()
        self.organizer = Organizer(self.file_manager)
        self.history = HistoryRepository(HISTORY_DB_PATH)
        self._busy = threading.Lock()
        self._pending_documents: list[DocumentRecord] = []
        self.state = self._build_initial_state()
        self.watcher = FileWatcher(self._handle_watcher_event)
        self._sync_known_hints_with_categories()
        self._bootstrap()

    def _build_initial_state(self) -> dict[str, object]:
        persisted = load_runtime_state()
        return {
            "config": asdict(self.config),
            "pending_groups": persisted.get("pending_groups", []),
            "categories": load_categories(),
            "recent_files": [],
            "duplicate_groups": persisted.get("duplicate_groups", []),
            "unclassified": persisted.get("unclassified", []),
            "last_summary": persisted.get("last_summary", {}),
            "agent": {
                "active": False,
                "paused": False,
                "started_at": persisted.get("agent_started_at", ""),
                "last_run": persisted.get("last_run", ""),
            },
            "status_message": "",
        }

    def _bootstrap(self) -> None:
        self.refresh_runtime_state()
        if self.config.watch_path and self.config.watch_path.exists():
            self.start_agent()

    def snapshot(self) -> dict[str, object]:
        return json.loads(json.dumps(self.state, ensure_ascii=False))

    def has_configuration(self) -> bool:
        return self.config.is_configured and self.config.watch_path is not None and self.config.watch_path.exists()
    
    def _require_watch_folder(self) -> Path:
        if not self.config.watch_path or not self.config.watch_path.exists():
            raise RuntimeError(
                f"La carpeta de monitoreo no existe o no está configurada: "
                f"'{self.config.watch_folder}'"
                )
        return self.config.watch_path

    def update_config(self, watch_folder: str, auto_rename: bool, detect_duplicates: bool) -> None:
        clean_watch_folder = watch_folder.strip()
        folder_changed = self.config.watch_folder.strip() != clean_watch_folder
        if folder_changed:
            self.stop_agent()
            self._reset_workspace_state()

        self.config = UserConfig(
            watch_folder=clean_watch_folder,
            auto_rename=auto_rename,
            detect_duplicates=detect_duplicates,
            similarity_threshold=self.config.similarity_threshold,
        )
        save_user_config(self.config)
        self.state["config"] = asdict(self.config)
        self.state["status_message"] = (
            "Configuracion actualizada. Ejecuta un analisis inicial para confirmar los grupos sugeridos."
            if folder_changed
            else "Configuracion actualizada."
        )
        self.refresh_runtime_state()
        logger.info(
            "Configuracion actualizada | carpeta=%s | auto_rename=%s | detect_duplicates=%s | folder_changed=%s",
            self.config.watch_folder,
            self.config.auto_rename,
            self.config.detect_duplicates,
            folder_changed,
        )
        self._notify()

    def analyze_initial(self) -> list[dict[str, object]]:
        watch_path = self._require_watch_folder()
        documents = self._collect_documents(
            self._incoming_files(watch_path),
            use_cover_text=True,
            include_embeddings=True,
        )
        if not documents:
            self._pending_documents = []
            self.state["pending_groups"] = []
            self.state["status_message"] = "No se encontraron archivos nuevos para analizar."
            self._persist_runtime()
            self._notify()
            logger.info("Analisis inicial sin archivos nuevos | carpeta=%s", watch_path)
            return []

        labels = self.clusterer.cluster([document.embedding for document in documents])
        grouped_documents: dict[int, list[DocumentRecord]] = defaultdict(list)
        for label, document in zip(labels, documents):
            grouped_documents[label].append(document)

        proposals: list[GroupProposal] = []
        for index, documents_in_group in enumerate(grouped_documents.values(), start=1):
            keywords = self._keywords_for_documents(documents_in_group)
            representative_path = Path(documents_in_group[0].path) if documents_in_group else None
            group_text = " ".join(doc.text or "" for doc in documents_in_group[:3])
            name = self._suggest_category_name(keywords, text=group_text)
            proposals.append(
                GroupProposal(
                    group_id=f"group-{index}",
                    suggested_name=name,
                    keywords=keywords,
                    file_ids=[document.doc_id for document in documents_in_group],
                    file_names=[document.name for document in documents_in_group],
                )
            )

        self.state["pending_groups"] = [asdict(proposal) for proposal in proposals]
        self._pending_documents = documents
        self.state["status_message"] = f"Se detectaron {len(proposals)} grupos para confirmar."
        self._persist_runtime()
        logger.info("Analisis inicial completado | carpeta=%s | grupos=%s | documentos=%s", watch_path, len(proposals), len(documents))
        self._notify()
        return self.state["pending_groups"]

    def confirm_groups(self, mapping: dict[str, str]) -> dict[str, object]:
        pending_groups = self.state.get("pending_groups", [])
        if not pending_groups:
            return {}

        proposals = {group["group_id"]: group for group in pending_groups}
        documents = list(self._pending_documents)
        if not documents:
            return {}

        # ✅ Mismo nombre = misma carpeta (fusión, no duplicado numerado)
        group_to_folder: dict[str, str] = {}
        for group_id, group in proposals.items():
            name = (mapping.get(group_id) or group["suggested_name"]).strip()
            if not name:
                name = group["suggested_name"]
            group_to_folder[group_id] = name

        # Construir categories_payload sin duplicar nombres
        seen_names: dict[str, dict] = {}
        for group_id, group in proposals.items():
            name = group_to_folder[group_id]
            if name in seen_names:
                # ✅ Fusionar keywords y files en la entrada existente
                seen_names[name]["keywords"] = list(set(
                    seen_names[name]["keywords"] + group["keywords"]
                ))
                seen_names[name]["files"].extend(group["file_names"])
            else:
                seen_names[name] = {
                    "name": name,
                    "keywords": list(group["keywords"]),
                    "files": list(group["file_names"]),
                }

        categories_payload = list(seen_names.values())
        save_categories(categories_payload)
        self.state["categories"] = categories_payload
        self._sync_known_hints_with_categories()

        # Asignar carpeta a cada documento por doc_id
        assignment_by_doc: dict[str, str] = {}
        for group_id, group in proposals.items():
            folder_name = group_to_folder[group_id]
            for document_id in group["file_ids"]:
                assignment_by_doc[document_id] = folder_name

        for document in documents:
            document.assigned_category = assignment_by_doc.get(document.doc_id)

        summary = self._organize_documents(documents, explicit_assignments=assignment_by_doc)
        self._pending_documents = []
        self.state["pending_groups"] = []
        self.refresh_runtime_state(last_summary=summary)
        self.start_agent()
        logger.info("Grupos confirmados | categorias=%s | organizados=%s", len(categories_payload), summary.get("organized", 0))
        self._notify()
        return summary

    def organize_now(self) -> dict[str, object]:
        watch_path = self._require_watch_folder()
        categories = load_categories()
        
        # ✅ Verificar que haya categorías CON keywords, no solo que existan
        has_usable_categories = any(
            cat.get("keywords") or cat.get("files")
            for cat in categories
        )
        # Las DEFAULT_ACADEMIC_CATEGORIES tienen keywords → has_usable_categories=True
        # Esto evita el bloqueo innecesario de "confirma los grupos"
        
        if not categories:
            proposals = self.analyze_initial()
            if proposals:
                self.state["status_message"] = "Confirma los grupos sugeridos para continuar."
                self._notify()
                return self._empty_summary()
        
        incoming = self._collect_documents(
            self._incoming_files(watch_path),
            use_cover_text=True,
            include_embeddings=False,
        )
        if not incoming:
            self.state["status_message"] = "No hay archivos nuevos para organizar."
            self._notify()
            return self.state.get("last_summary", {})

        summary = self._organize_documents(incoming)
        self.refresh_runtime_state(last_summary=summary)
        self._notify()
        return summary

    def toggle_agent(self) -> None:
        if not self.watcher.is_running:
            self.start_agent()
            return
        if self.watcher.paused:
            self.watcher.resume()
            self.state["agent"]["paused"] = False
            self.state["status_message"] = "El agente reanudo el monitoreo."
        else:
            self.watcher.pause()
            self.state["agent"]["paused"] = True
            self.state["status_message"] = "El agente se encuentra en pausa."
        self._persist_runtime()
        logger.info("Cambio de estado del agente | activo=%s | pausado=%s", self.watcher.is_running, self.watcher.paused)
        self._notify()

    def start_agent(self) -> None:
        if not self.has_configuration():
            return
        watch_path = self._require_watch_folder()
        self.file_manager.ensure_folder(watch_path / DEFAULT_DUPLICATES_FOLDER_NAME)
        self.watcher.start(watch_path)
        self.state["agent"]["active"] = True
        self.state["agent"]["paused"] = False
        self.state["agent"]["started_at"] = datetime.now().strftime("%H:%M:%S")
        self._persist_runtime()
        logger.info("Agente iniciado | carpeta=%s", watch_path)

    def stop_agent(self) -> None:
        self.watcher.stop()
        self.state["agent"]["active"] = False
        self.state["agent"]["paused"] = False
        self._persist_runtime()
        logger.info("Agente detenido")
        self._notify()

    def manual_categories(self) -> list[str]:
        categories = self.state.get("categories", [])
        return [category["name"] for category in categories]

    def create_category(self, name: str) -> None:
        clean_name = name.strip()
        if not clean_name:
            return
        categories = load_categories()
        if all(category["name"] != clean_name for category in categories):
            categories.append({"name": clean_name, "keywords": [], "files": []})
            save_categories(categories)
            self.state["categories"] = categories

    def manual_classify(self, file_path: str, category_name: str, new_folder_name: str = "") -> None:
        if new_folder_name.strip():
            self.create_category(new_folder_name.strip())
            category_name = new_folder_name.strip()

        path = Path(file_path)
        if not path.exists():
            return

        documents = self._collect_documents(
            [path],
            use_cover_text=True,
            include_embeddings=False,
        )
        if not documents:
            self.state["status_message"] = f"No fue posible procesar {path.name} para clasificarlo manualmente."
            self._notify()
            return

        document = documents[0]
        destination = self.organizer.organize(
            path,
            self._require_watch_folder(),
            category_name,
            auto_rename=self.config.auto_rename,
            keywords=document.keywords,
        )
        self.history.add_record(
            HistoryRecord(
                source=str(path),
                destination=str(destination),
                action="manual_classified",
                category=category_name,
                confidence=1.0,
            )
        )
        self._learn_from_document(category_name, document, destination_path=destination)
        self.state["status_message"] = f"{path.name} fue movido manualmente a {category_name}."
        self.refresh_runtime_state()
        logger.info("Archivo clasificado manualmente | archivo=%s | categoria=%s", path, category_name)
        self._notify()

    def delete_duplicates(self, selected_paths: list[str]) -> None:
        removed = 0
        for path_str in selected_paths:
            path = Path(path_str)
            if path.exists():
                self.file_manager.delete_file(path)
                removed += 1
                self.history.add_record(
                    HistoryRecord(source=path_str, destination="", action="duplicate_deleted", category="")
                )
        self.state["status_message"] = f"Se eliminaron {removed} archivos duplicados."
        self.refresh_runtime_state()
        logger.info("Duplicados eliminados | cantidad=%s", removed)
        self._notify()

    def restore_duplicates(self, selected_paths: list[str]) -> None:
        restored = 0
        for path_str in selected_paths:
            source = Path(path_str)
            if not source.exists():
                continue
            original_path = self._original_duplicate_path(path_str)
            destination = self.file_manager.move_file(source, original_path or (self._require_watch_folder() / source.name))
            restored += 1
            self.history.add_record(
                HistoryRecord(source=path_str, destination=str(destination), action="duplicate_restored", category="")
            )
        self.state["status_message"] = f"Se restauraron {restored} archivos al directorio principal."
        self.refresh_runtime_state()
        logger.info("Duplicados restaurados | cantidad=%s", restored)
        self._notify()

    def refresh_runtime_state(self, last_summary: dict[str, object] | None = None) -> None:
        stats = self.history.overall_stats()
        recent_records = self.history.recent_records(limit=6)
        self.state["recent_files"] = self._format_recent_records(recent_records)
        self.state["categories"] = load_categories()
        self.state["duplicate_groups"] = self._load_duplicate_groups_from_runtime()
        self.state["unclassified"] = self._scan_unclassified()
        if last_summary is not None:
            self.state["last_summary"] = last_summary
        elif not self.state.get("last_summary"):
            self.state["last_summary"] = self._empty_summary()

        self.state["stats"] = {
            "total_organized": int(stats["total_organized"]),
            "duplicates_detected": int(stats["duplicates_detected"]),
            "average_confidence": round(stats["average_confidence"] * 100, 1),
            "folders_created": len(self.state["categories"]),
        }
        self.state["config"] = asdict(self.config)
        self._persist_runtime()

    def _collect_documents(
        self,
        file_paths: list[Path],
        *,
        use_cover_text: bool = True,
        include_embeddings: bool = False,
    ) -> list[DocumentRecord]:
        documents = []
        for file_path in file_paths:
            if not file_path.exists() or not file_path.is_file():
                continue
            extraction = (
                self.text_extractor.extract_cover(file_path)
                if use_cover_text
                else self.text_extractor.extract(file_path)
            )
            keywords = self.keyword_extractor.extract(extraction.text or file_path.stem)
            embedding = (
                self.embedder.embed(extraction.text or " ".join(keywords) or file_path.stem)
                if include_embeddings
                else []
            )
            try:
                digest = self.duplicate_detector.hash_file(file_path)
            except OSError:
                continue
            stat = file_path.stat()
            documents.append(
                DocumentRecord(
                    doc_id=uuid.uuid4().hex,
                    path=str(file_path),
                    name=file_path.name,
                    extension=file_path.suffix.lower(),
                    size_bytes=stat.st_size,
                    modified_at=stat.st_mtime,
                    text=extraction.text,
                    keywords=keywords,
                    embedding=embedding,
                    hash_sha256=digest,
                    extraction_method=extraction.method,
                    extraction_note=extraction.note,
                )
            )
        return documents

    def _organize_documents(
        self,
        documents: list[DocumentRecord],
        *,
        explicit_assignments: dict[str, str] | None = None,
    ) -> dict[str, object]:
        all_texts = [doc.text for doc in documents if doc.text]
        if all_texts:
            self.keyword_extractor.fit_corpus(all_texts)
        start = time.perf_counter()
        explicit_assignments = explicit_assignments or {}
        watch_path = self._require_watch_folder()
        duplicates_folder = watch_path / DEFAULT_DUPLICATES_FOLDER_NAME
        existing = self._collect_documents(
            self._managed_files(watch_path),
            use_cover_text=False,
            include_embeddings=False,
        )

        duplicate_groups, duplicate_ids = self.duplicate_detector.detect(
            documents,
            existing if self.config.detect_duplicates else [],
        )

        categories = self._build_category_profiles(existing, load_categories())
        runtime_hints = self._build_runtime_hint_map(categories)
        self._train_neural_classifier(categories, existing)
        cycle = CycleSummary(detected=len(documents))
        folder_counter: Counter[str] = Counter()
        confidence_values: list[float] = []
        persisted_duplicate_groups = []
        unclassified_notes = []

        for group in duplicate_groups:
            persisted_duplicate_groups.append(asdict(group))

        for document in documents:
            source = Path(document.path)
            # Procesar con contenido completo para clasificar con mejor precisión.
            self._ensure_full_text(document)
            if document.doc_id in duplicate_ids:
                duplicate_path = self.organizer.move_to_duplicates(source, duplicates_folder)
                self._update_duplicate_item_path(persisted_duplicate_groups, document.doc_id, duplicate_path, Path(document.path))
                cycle.duplicates += 1
                self.history.add_record(
                    HistoryRecord(
                        source=document.path,
                        destination=str(duplicate_path),
                        action="duplicate_moved",
                        category="",
                        confidence=1.0,
                    )
                )
                continue

            assigned = explicit_assignments.get(document.doc_id)
            confidence = 1.0 if assigned else 0.0

            if not assigned:
                assigned, confidence = self._classify_by_cover_subject(
                    document.text or "",
                    categories,
                    document_name=document.name,
                )

            if not assigned:
                multi_results = get_multi_categories(
                    document.text or "",
                    runtime_hints,
                )
                if multi_results:
                    assigned, confidence = multi_results[0]
                    if len(multi_results) > 1:
                        logger.info(
                            "Multi-categoría detectada: %s -> %s (alternativas: %s)",
                            document.name,
                            assigned,
                            [f"{c}({s:.2f})" for c, s in multi_results[1:]]
                        )

            if not assigned:
                neural_cover_text = f"{document.name} {document.text or ''}".strip()
                neural_label, neural_conf = self._predict_by_neural(neural_cover_text)
                if neural_label and neural_conf >= NEURAL_MIN_COVER_CONFIDENCE:
                    assigned, confidence = neural_label, neural_conf

            if not assigned:
                self._ensure_full_text(document)

            if not assigned:
                assigned, confidence = self._classify_by_cover_subject(
                    document.text or "",
                    categories,
                    document_name=document.name,
                )

            if not assigned:
                multi_results = get_multi_categories(
                    document.text or "",
                    runtime_hints,
                )
                if multi_results:
                    assigned, confidence = multi_results[0]

            if not assigned:
                neural_label, neural_conf = self._predict_by_neural(document.text or "")
                if neural_label and neural_conf >= NEURAL_MIN_CONTENT_CONFIDENCE:
                    assigned, confidence = neural_label, neural_conf

            if not assigned:
                if not document.embedding:
                    document.embedding = self.embedder.embed(
                        document.text or " ".join(document.keywords) or source.stem
                    )
                label, confidence = self.classifier.classify(
                    document.embedding,
                    {category.name: category.centroid for category in categories if category.centroid},
                    similarity_threshold=self.config.similarity_threshold,
                )
                assigned = label

            if not assigned:
                assigned, confidence = self._classify_by_keywords(document.keywords, categories)

            if not assigned:
                cycle.unclassified += 1
                unclassified_notes.append({
                    "path": document.path,
                    "name": document.name,
                    "reason": document.extraction_note or "No se encontró categoría.",
                    "keywords": document.keywords,
                })
                continue

            destination = self.organizer.organize(
                source,
                watch_path,
                assigned,
                auto_rename=self.config.auto_rename,
                keywords=document.keywords,
            )
            if destination is None:
                logger.warning("organize() retornó None para '%s', omitiendo.", source.name)
                cycle.unclassified += 1
                unclassified_notes.append({"path": document.path, "name": document.name, "reason": "El archivo no pudo moverse.", "keywords": document.keywords})
                continue

            self._update_duplicate_item_path(persisted_duplicate_groups, document.doc_id, destination, Path(document.path))
            folder_counter[assigned] += 1
            cycle.organized += 1
            if destination.name != source.name:
                cycle.renamed += 1
            confidence_values.append(confidence or 1.0)
            self.history.add_record(
                HistoryRecord(
                    source=document.path,
                    destination=str(destination),
                    action="organized",
                    category=assigned,
                    confidence=confidence or 1.0,
                    details=json.dumps({"keywords": document.keywords}, ensure_ascii=False),
                )
            )
            if (confidence or 0.0) >= LEARNING_CONFIDENCE_THRESHOLD:
                self._learn_from_document(assigned, document, destination_path=destination)

        cycle.precision = round((sum(confidence_values) / len(confidence_values)) * 100, 1) if confidence_values else 0.0
        cycle.duration_seconds = round(time.perf_counter() - start, 2)
        cycle.folders = [
            {"name": name, "count": count, "path": str(watch_path / name)}
            for name, count in sorted(folder_counter.items())
        ]

        summary = asdict(cycle)
        self.state["duplicate_groups"] = persisted_duplicate_groups
        self.state["unclassified"] = unclassified_notes
        self.state["last_summary"] = summary
        self.state["status_message"] = "Organizacion completada."
        self.state["agent"]["last_run"] = datetime.now().strftime("%H:%M:%S")
        self._persist_runtime()
        return summary

    def _build_category_profiles(
        self,
        managed_documents: list[DocumentRecord],
        persisted_categories: list[dict[str, object]],
    ) -> list[CategoryProfile]:
        by_name: dict[str, list[DocumentRecord]] = defaultdict(list)
        watch_path = self._require_watch_folder()
        for document in managed_documents:
            path = Path(document.path)
            if path.parent == watch_path:
                continue
            if path.parent.name == DEFAULT_DUPLICATES_FOLDER_NAME:
                continue
            by_name[path.parent.name].append(document)

        categories: list[CategoryProfile] = []
        for item in persisted_categories:
            name = str(item["name"])
            documents = by_name.get(name, [])
            keywords = self._keywords_for_documents(documents) or list(item.get("keywords", []))
            vectors = [document.embedding for document in documents if document.embedding]

            if vectors:
                computed_centroid = centroid(vectors)
            elif keywords:
                # ✅ Centroide sintético: embed las keywords como texto
                synthetic_text = " ".join(keywords)
                computed_centroid = self.embedder.embed(synthetic_text)
            else:
                computed_centroid = []

            categories.append(
                CategoryProfile(
                    name=name,
                    keywords=keywords,
                    centroid=computed_centroid,
                    files=[document.path for document in documents],
                )
            )
        return categories

    def _sync_known_hints_with_categories(self) -> None:
        for category in load_categories():
            name = str(category.get("name", "")).strip()
            if not name or name not in KNOWN_CATEGORY_HINTS:
                continue
            keywords = {
                str(token).strip().lower()
                for token in category.get("keywords", [])
                if str(token).strip()
            }
            KNOWN_CATEGORY_HINTS[name].update(keywords)

    def _build_runtime_hint_map(self, categories: list[CategoryProfile]) -> dict[str, set[str]]:
        """Construye hints dinámicos para todas las categorías activas."""
        runtime_hints: dict[str, set[str]] = {}

        # Base: hints globales conocidos.
        for name, hints in KNOWN_CATEGORY_HINTS.items():
            runtime_hints[name] = set(hints)

        for category in categories:
            name = category.name.strip()
            if not name:
                continue
            bucket = runtime_hints.setdefault(name, set())

            # Incluir tokens del nombre de categoría.
            normalized_name = self._normalize_for_match(name)
            name_tokens = [token for token in normalized_name.split() if len(token) >= 3]
            bucket.update(name_tokens)
            if normalized_name:
                bucket.add(normalized_name.replace(" ", ""))

            # Incluir keywords aprendidas/configuradas.
            for keyword in category.keywords:
                normalized_kw = self._normalize_for_match(str(keyword))
                if not normalized_kw:
                    continue
                bucket.add(normalized_kw)
                bucket.add(normalized_kw.replace(" ", ""))

        return runtime_hints

    def _keywords_for_documents(self, documents: list[DocumentRecord], limit: int = 5) -> list[str]:
        counter: Counter[str] = Counter()
        for document in documents:
            counter.update(document.keywords)
        return [token for token, _count in counter.most_common(limit)]

    def _build_neural_training_samples(
        self,
        categories: list[CategoryProfile],
        managed_documents: list[DocumentRecord],
) -> list[tuple[str, str]]:
        samples: list[tuple[str, str]] = []

        for category in categories:
            if category.keywords:
                kw_text = " ".join(category.keywords)
                samples.append((f"{category.name} {kw_text} {kw_text}", category.name))
                samples.append((f"materia {category.name} proyecto final {kw_text}", category.name))
                samples.append((f"portada {category.name} unidad reporte {kw_text}", category.name))
            else:
                samples.append((category.name, category.name))

            hint_words = list(KNOWN_CATEGORY_HINTS.get(category.name, set()))
            if hint_words:
                hint_slice = " ".join(hint_words[:40])
                samples.append((f"{category.name} {hint_slice}", category.name))

        for document in managed_documents:
            doc_path = Path(document.path)
            label = doc_path.parent.name
            if not label or label == DEFAULT_DUPLICATES_FOLDER_NAME:
                continue
            text = (document.text or "").strip()
            if not text:
                text = f"{doc_path.stem} {' '.join(document.keywords)}".strip()
            if text:
                samples.append((text[:3000], label))

        history_records = self.history.recent_records(limit=800)
        for record in history_records:
            if record.get("action") not in {"organized", "manual_classified"}:
                continue
            label = str(record.get("category", "")).strip()
            if not label:
                continue
            source_name = Path(str(record.get("source", ""))).stem
            destination_name = Path(str(record.get("destination", ""))).stem
            details = record.get("details", {})
            detail_keywords = []
            if isinstance(details, dict):
                detail_keywords = [str(item) for item in details.get("keywords", [])]
            text = f"{source_name} {destination_name} {' '.join(detail_keywords)}".strip()
            if text:
                samples.append((text[:2000], label))
        return samples

    def _train_neural_classifier(
        self,
        categories: list[CategoryProfile],
        managed_documents: list[DocumentRecord],
    ) -> None:
        samples = self._build_neural_training_samples(categories, managed_documents)
        
        if not self.neural_classifier.ready:
            logger.info("Clasificador neuronal no inicializado, ejecutando pre-entrenamiento...")
            pre_trained = self.neural_classifier.pre_train()
            if pre_trained and samples:
                logger.info("Aplicando fine-tuning con %d muestras del usuario", len(samples))
                self.neural_classifier.train_with_fine_tuning(samples)
        else:
            if samples:
                logger.info("Re-entrenando con fine-tuning usando %d muestras", len(samples))
                self.neural_classifier.train_with_fine_tuning(samples)
            else:
                logger.debug("No hay muestras nuevas, manteniendo clasificador existente")

        trained = self.neural_classifier.ready
        logger.info(
            "Entrenamiento expert neural | muestras=%d | categorias=%d | activo=%s",
            len(samples),
            len(categories),
            trained,
        )

    def _predict_by_neural(self, text: str) -> tuple[str | None, float]:
        prediction = self.neural_classifier.predict(text)
        return prediction.label, prediction.confidence

    def _ensure_full_text(self, document: DocumentRecord) -> None:
        if document.text and not document.extraction_method.endswith("_cover"):
            return
        source = Path(document.path)
        extraction = self.text_extractor.extract(source)
        if extraction.text:
            document.text = extraction.text
        document.extraction_method = extraction.method
        document.extraction_note = extraction.note
        document.keywords = self.keyword_extractor.extract(document.text or source.stem)

    def _learn_from_document(
        self,
        category_name: str,
        document: DocumentRecord,
        *,
        destination_path: Path | None = None,
    ) -> None:
        if not category_name:
            return

        learned_tokens = list(document.keywords)
        learned_tokens.extend(self._tokens_from_text(document.name))
        if document.text:
            learned_tokens.extend(self._tokens_from_text(document.text[:1500]))
        self._upsert_category_learning(
            category_name,
            learned_tokens,
            destination_path=destination_path,
        )

    def _upsert_category_learning(
        self,
        category_name: str,
        tokens: list[str],
        *,
        destination_path: Path | None = None,
    ) -> None:
        clean_name = category_name.strip()
        if not clean_name:
            return

        cleaned_tokens = []
        seen = set()
        for token in tokens:
            normalized = token.strip().lower()
            if len(normalized) < LEARNING_MIN_TOKEN_LEN:
                continue
            if not normalized.isalpha():
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            cleaned_tokens.append(normalized)

        categories = load_categories()
        category_entry = next((item for item in categories if item.get("name") == clean_name), None)
        if category_entry is None:
            category_entry = {"name": clean_name, "keywords": [], "files": []}
            categories.append(category_entry)

        existing_keywords = [str(k).strip().lower() for k in category_entry.get("keywords", []) if str(k).strip()]
        merged_keywords = []
        existing_seen = set()
        for token in [*existing_keywords, *cleaned_tokens]:
            if token in existing_seen:
                continue
            existing_seen.add(token)
            merged_keywords.append(token)
        category_entry["keywords"] = merged_keywords[:LEARNING_KEYWORDS_LIMIT]

        if destination_path is not None:
            existing_files = [str(p) for p in category_entry.get("files", []) if str(p).strip()]
            destination_str = str(destination_path)
            if destination_str not in existing_files:
                existing_files.append(destination_str)
            category_entry["files"] = existing_files[-LEARNING_KEYWORDS_LIMIT:]

        save_categories(categories)
        self.state["categories"] = categories

        if clean_name in KNOWN_CATEGORY_HINTS:
            KNOWN_CATEGORY_HINTS[clean_name].update(category_entry["keywords"])

    def _tokens_from_text(self, text: str, *, limit: int = 20) -> list[str]:
        if not text:
            return []
        tokens = re.findall(r"[a-zA-ZáéíóúÁÉÍÓÚñÑ]{4,}", text.lower())
        unique_tokens = []
        seen = set()
        for token in tokens:
            if token in seen:
                continue
            seen.add(token)
            unique_tokens.append(token)
            if len(unique_tokens) >= limit:
                break
        return unique_tokens

    def _suggest_category_name(self, keywords: list[str], text: str = "") -> str:
            # Paso 1: buscar hints en el texto si está disponible
            if text:
                hint_label, hint_conf = classify_by_hints(text, KNOWN_CATEGORY_HINTS)
                if hint_label and hint_conf >= 0.80:
                    return hint_label
    
            # Paso 2: buscar en keywords directamente contra hints (REQUIERE minimo 2 hits)
            keyword_set = set(kw.lower() for kw in keywords)
            best_name = None
            best_hits = 0
            for name, hint_words in KNOWN_CATEGORY_HINTS.items():
                hits = len(keyword_set.intersection(hint_words))
                if hits > best_hits:
                    best_name  = name
                    best_hits  = hits
    
            # REQUIERE al menos 2 keywords en comun para clasificar
            if best_name and best_hits >= 2:
                return best_name
    
            # Si no hay suficientes coincidencias, generar nombre desde keywords
            # NO devolver None - siempre debe haber un nombre
            if keywords:
                name = generate_category_name(keywords)
                if name == "Archivos Varios":
                    name = title_from_keywords(keywords, fallback=f"Grupo {len(keywords)}")
                logger.warning(
                    "Clasificacion por keywords: keywords=%s, best_hits=%d, name=%s",
                    keywords[:3], best_hits, name
                )
                return name
            
            # Si ni siquiera hay keywords, usar nombre genérico
            logger.warning("Sin keywords para clasificar, usando fallback")
            return "Archivos Varios"
            return title_from_keywords(keywords, fallback="Grupo Academico")

    def _classify_by_cover_subject(
        self,
        text: str,
        categories: list[CategoryProfile],
        document_name: str = "",
    ) -> tuple[str | None, float]:
        if not text or not categories:
            if not document_name:
                return None, 0.0

        searchable = f"{document_name} {text[:3500]}".strip()
        cover_text = self._normalize_for_match(searchable)
        if not cover_text:
            return None, 0.0

        # Regla fuerte: extraer candidatos de materia (con o sin prefijo) y mapearlos.
        for candidate in self._extract_subject_candidates(text, document_name=document_name):
            explicit_match, explicit_score = self._best_category_match(candidate, categories)
            if explicit_match and explicit_score >= 0.78:
                return explicit_match, min(0.995, 0.94 + (explicit_score - 0.78) * 0.20)

        best_name = None
        best_hits = 0
        best_ratio = 0.0
        best_token_count = 0
        for category in categories:
            category_normalized = self._normalize_for_match(category.name)
            tokens = [token for token in re.split(r"[^a-z0-9]+", category_normalized) if len(token) >= 3]
            if not tokens:
                continue
            # Match exacto de la frase completa de la materia en nombre/portada.
            if category_normalized and category_normalized in cover_text:
                return category.name, 0.995
            hits = sum(1 for token in tokens if token in cover_text)
            ratio = hits / max(len(tokens), 1)
            if hits > best_hits:
                best_hits = hits
                best_name = category.name
                best_token_count = len(tokens)
                best_ratio = ratio
            elif hits == best_hits and ratio > best_ratio:
                best_name = category.name
                best_token_count = len(tokens)
                best_ratio = ratio

        if best_name is None:
            return None, 0.0
        required_hits = 2 if best_token_count >= 3 else 1
        if best_hits >= required_hits and best_ratio >= 0.5:
            confidence = min(0.97, 0.72 + best_hits * 0.10 + best_ratio * 0.08)
            return best_name, confidence

        # Fuzzy fallback sobre portada/nombre cuando la coincidencia no es literal.
        fuzzy_match, fuzzy_score = self._best_category_match(cover_text, categories)
        if fuzzy_match and fuzzy_score >= 0.84:
            return fuzzy_match, min(0.985, 0.86 + (fuzzy_score - 0.84) * 0.30)
        return None, 0.0

    def _extract_subject_candidates(self, text: str, *, document_name: str = "") -> list[str]:
        candidates: list[str] = []
        source = (text or "")[:5000]

        # 1) Patrones explícitos tipo "Materia: X"
        patterns = (
            r"(?im)\b(?:materia|asignatura|curso|unidad de aprendizaje)\b\s*[:\-]\s*([^\n\r]{3,120})",
            r"(?im)\b(?:materia|asignatura|curso)\b\s+([^\n\r]{3,120})",
        )
        for pattern in patterns:
            match = re.search(pattern, source)
            if match:
                candidate = self._normalize_for_match(match.group(1))
                if len(candidate) >= 4:
                    candidates.append(candidate)

        # 2) Primeras líneas de portada como posibles títulos de materia (sin prefijo)
        raw_lines = [line.strip() for line in source.splitlines()[:20] if line.strip()]
        blocked_words = {
            "tecnologico", "instituto", "universidad", "campus", "semestre",
            "grupo", "docente", "profesor", "alumno", "nombre", "matricula",
            "portada", "proyecto", "reporte", "practica", "equipo", "fecha",
        }
        for line in raw_lines:
            normalized = self._normalize_for_match(line)
            if len(normalized) < 6:
                continue
            tokens = normalized.split()
            if len(tokens) > 8:
                continue
            if sum(1 for token in tokens if token in blocked_words) >= max(1, len(tokens) // 2):
                continue
            candidates.append(normalized)

        # 3) Nombre de archivo también es candidato
        if document_name:
            filename_candidate = self._normalize_for_match(Path(document_name).stem)
            if len(filename_candidate) >= 4:
                candidates.append(filename_candidate)

        # Deduplicar preservando orden
        unique: list[str] = []
        seen = set()
        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            unique.append(candidate)
        return unique

    def _best_category_match(
        self,
        normalized_text: str,
        categories: list[CategoryProfile],
    ) -> tuple[str | None, float]:
        if not normalized_text:
            return None, 0.0
        best_name: str | None = None
        best_score = 0.0
        for category in categories:
            category_name = self._normalize_for_match(category.name)
            if not category_name:
                continue
            score = SequenceMatcher(None, normalized_text, category_name).ratio()
            # Si el nombre de categoría está contenido, subir score.
            if category_name in normalized_text:
                score = max(score, 0.99)
            if score > best_score:
                best_score = score
                best_name = category.name
        return best_name, best_score

    def _normalize_for_match(self, text: str) -> str:
        if not text:
            return ""
        normalized = unicodedata.normalize("NFKD", text)
        normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        normalized = normalized.lower()
        normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _classify_by_keywords(
        self,
        document_keywords: list[str],
        categories: list[CategoryProfile],
    ) -> tuple[str | None, float]:
        document_set = set(document_keywords)
        best_name = None
        best_score = 0.0
        if not document_set:
            return None, 0.0

        for category in categories:
            category_set = set(category.keywords)
            if not category_set:
                continue
            intersection = len(document_set.intersection(category_set))
            union = len(document_set.union(category_set))
            score = intersection / union if union else 0.0
            if score > best_score:
                best_name = category.name
                best_score = score

        if best_name and best_score >= 0.08:
            return best_name, best_score
        return None, best_score

    def _incoming_files(self, watch_path: Path) -> list[Path]:
        if not watch_path.exists():
            return []
        return [child for child in watch_path.iterdir() if child.is_file()]

    def _managed_files(self, watch_path: Path) -> list[Path]:
        files = []
        if not watch_path.exists():
            return files
        for category in load_categories():
            folder = watch_path / category["name"]
            if folder.exists():
                files.extend(child for child in folder.iterdir() if child.is_file())
        return files

    def _scan_unclassified(self) -> list[dict[str, object]]:
        if not self.has_configuration():
            return []
        watch_path = self._require_watch_folder()
        documents = self._collect_documents(
            self._incoming_files(watch_path),
            use_cover_text=True,
            include_embeddings=False,
        )
        return [
            {
                "path": document.path,
                "name": document.name,
                "reason": document.extraction_note or "No fue posible determinar una categoria automaticamente.",
                "keywords": document.keywords,
                "meta": f"{round(document.size_bytes / 1024, 1)} KB · {document.extension or 'archivo'}",
            }
            for document in documents
        ]

    def _format_recent_records(self, records: list[dict[str, object]]) -> list[dict[str, object]]:
        recent = []
        for record in records:
            if record["action"] not in {"organized", "manual_classified"}:
                continue
            source_name = Path(record["source"]).name
            destination_name = Path(record["destination"]).name
            timestamp = datetime.fromisoformat(record["timestamp"])
            recent.append(
                {
                    "name": destination_name,
                    "original": f"Origen: {source_name}",
                    "category": record["category"] or "General",
                    "time": timestamp.strftime("%d %b %H:%M"),
                }
            )
        return recent

    def _empty_summary(self) -> dict[str, object]:
        return asdict(CycleSummary())

    def _load_duplicate_groups_from_runtime(self) -> list[dict[str, object]]:
        persisted = load_runtime_state()
        return self._prune_duplicate_groups(persisted.get("duplicate_groups", []))

    def _prune_duplicate_groups(self, groups: list[dict[str, object]]) -> list[dict[str, object]]:
        clean_groups = []
        for group in groups:
            items = []
            for item in group.get("items", []):
                current_path = item.get("current_path", "")
                if not current_path or not Path(current_path).exists():
                    continue
                items.append(item)
            if len(items) < 2:
                continue
            if not any(item.get("state") == "Duplicado" for item in items):
                continue
            clean_group = dict(group)
            clean_group["items"] = items
            clean_groups.append(clean_group)
        return clean_groups

    def _reset_workspace_state(self) -> None:
        empty_summary = self._empty_summary()
        save_categories([])
        self._pending_documents = []
        self.state["pending_groups"] = []
        self.state["categories"] = []
        self.state["duplicate_groups"] = []
        self.state["unclassified"] = []
        self.state["last_summary"] = empty_summary
        self.state["agent"]["started_at"] = ""
        self.state["agent"]["last_run"] = ""
        save_runtime_state(
            {
                "pending_groups": [],
                "duplicate_groups": [],
                "unclassified": [],
                "last_summary": empty_summary,
                "agent_started_at": "",
                "last_run": "",
            }
        )

    def _update_duplicate_item_path(
        self,
        duplicate_groups: list[dict[str, object]],
        doc_id: str,
        current_path: Path,
        original_path: Path,
    ) -> None:
        for group in duplicate_groups:
            for item in group.get("items", []):
                if item.get("doc_id") != doc_id:
                    continue
                item["current_path"] = str(current_path)
                item["original_path"] = str(original_path)
                meta = item.get("meta", "")
                if "·" in meta:
                    parts = meta.split("·")
                    item["meta"] = "·".join(parts[:-1] + [f" {current_path}"])
                else:
                    item["meta"] = f"{current_path}"

    def _original_duplicate_path(self, current_path: str) -> Path | None:
        for group in self.state.get("duplicate_groups", []):
            for item in group.get("items", []):
                if item.get("current_path") == current_path:
                    original = item.get("original_path")
                    if original:
                        return Path(original)
        return None

    def _persist_runtime(self) -> None:
        payload = {
            "pending_groups": self.state.get("pending_groups", []),
            "duplicate_groups": self.state.get("duplicate_groups", []),
            "unclassified": self.state.get("unclassified", []),
            "last_summary": self.state.get("last_summary", {}),
            "agent_started_at": self.state["agent"].get("started_at", ""),
            "last_run": self.state["agent"].get("last_run", ""),
        }
        save_runtime_state(payload)

    def _handle_watcher_event(self) -> None:
        if not self._busy.acquire(blocking=False):
            logger.debug("Watcher: evento ignorado, organización en curso")
            return
        try:
            self.watcher.pause()
            self.organize_now()
        except Exception:
            logger.exception("Error durante la ejecución del watcher")
        finally:
            self._busy.release()
            self.watcher.resume()

    def _notify(self) -> None:
        if self.notify_callback:
            self.notify_callback()
