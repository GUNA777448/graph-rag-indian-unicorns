# 🦄 Indian Unicorns Graph RAG

A **Graph RAG (Retrieval-Augmented Generation)** system for querying Indian Unicorn Startups data using Knowledge Graphs, local LLM, and an interactive UI.

## 🎯 Why Graph RAG over Traditional RAG?

| Aspect | Traditional RAG | Graph RAG |
|--------|----------------|-----------|
| **Retrieval** | Semantic similarity | Relationship traversal |
| **Context** | Text chunks | Structured entities + relations |
| **Multi-hop** | ❌ Fails | ✅ Native support |
| **Explainability** | Black box | Traceable paths |
| **Accuracy** | Hallucination-prone | Grounded in facts |

## 📊 Knowledge Graph Schema

```
┌─────────────┐     OPERATES_IN     ┌─────────┐     HAS_SUBSECTOR     ┌───────────┐
│   Company   │────────────────────▶│  Sector │─────────────────────▶│ SubSector │
└─────────────┘                     └─────────┘                       └───────────┘
      │                                   
      │ LOCATED_IN                        
      ▼                                   
┌─────────────┐                           
│  Location   │                           
└─────────────┘                           
      ▲                                   
      │ INVESTED_IN                       
┌─────────────┐                           
│  Investor   │
└─────────────┘
```

## 🔧 Tech Stack

- **Knowledge Graph**: Neo4j
- **LLM**: Ollama + Mistral (Local)
- **UI**: Streamlit
- **Language**: Python

## 📈 Dataset Stats

- 102 Unicorn Companies
- 200+ Investors
- 15 Sectors & Sub-sectors
- 20+ Locations
- 500+ Relationships

## 🚀 Quick Start

### Prerequisites

1. **Neo4j** - Install and run Neo4j locally
2. **Ollama** - Install and run Ollama with Mistral model

```bash
# Install Ollama and pull Mistral
ollama pull mistral
ollama serve
```

### Installation

```bash
# Clone the repository
git clone https://github.com/GUNA777448/indian-unicorns-graph-rag.git
cd indian-unicorns-graph-rag

# Install dependencies
pip install neo4j pandas streamlit requests

# Update Neo4j credentials in app.py and data/build_kg.py
NEO4J_PASSWORD = "your_password"
```

### Build the Knowledge Graph

```bash
cd data
python build_kg.py
```

### Run the Application

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## 💡 Sample Queries

- "Tell me about Flipkart"
- "Which companies has Tiger Global invested in?"
- "List top 5 Fintech unicorns"
- "Companies located in Bangalore"
- "Compare CRED and PhonePe"
- "Who are the top investors?"

## 📁 Project Structure

```
indian-unicorns-graph-rag/
├── app.py                          # Streamlit UI + RAG logic
├── data/
│   ├── get_data.py                 # Download dataset from Kaggle
│   ├── build_kg.py                 # Build Neo4j Knowledge Graph
│   ├── sample_queries.cypher       # Sample Cypher queries
│   └── Indian Unicorn startups 2023 updated.csv
└── README.md
```

## 🔍 Sample Cypher Queries

```cypher
-- Top investors by portfolio value
MATCH (i:Investor)-[:INVESTED_IN]->(c:Company)
WHERE c.currentValuation IS NOT NULL
RETURN i.name as Investor, 
       count(c) as Companies,
       round(sum(c.currentValuation) * 10) / 10 as PortfolioValue
ORDER BY PortfolioValue DESC
LIMIT 10;

-- Find co-investors
MATCH (i1:Investor)-[:INVESTED_IN]->(c:Company)<-[:INVESTED_IN]-(i2:Investor)
WHERE i1.name < i2.name
RETURN i1.name, i2.name, count(c) as SharedInvestments
ORDER BY SharedInvestments DESC
LIMIT 10;
```

## 📄 License

MIT License

## 🙏 Acknowledgments

- Dataset: [Indian Unicorn Startups 2023](https://www.kaggle.com/datasets/mlvprasad/indian-unicorn-startups-2023-june-updated) by MLV Prasad on Kaggle
