# Project 8 · Ask your data with AI

> ⚠️ **Fictional data.** It uses the same made-up sales as [project 6](../06-sql-ventas/).

## The problem
To get an answer from the sales database you have to write SQL, or calculate it by hand. Most people in an SME can't do either, so the data sits there unused.

## The solution
A small local web app: you type a question in plain language, AI (**Google Gemini**) turns it into SQL, **you predict the result**, and only then does the database run it.

```mermaid
flowchart LR
    A[Question in plain language] --> B[Gemini writes the SQL]
    B --> C[You read it and predict the result]
    C --> D[SQLite runs it, read-only]
    D --> E[Table + optional AI explanation]
```

1. **`ia_sql.py`** (the logic):
   - to write the SQL, it sends Gemini your question and the **table's structure** (column names, plus the possible values of `producto`, `talla` and `moneda`), not the sales themselves;
   - receives the SQL and tidies it into several lines so it's easy to read (if anything doesn't add up, it leaves the SQL untouched);
   - runs it with **two locks**: a filter that only accepts read queries (`SELECT`), and the database opened in read-only mode, which blocks any write that might get past the filter;
   - only if you click "explain", sends Gemini the question, the SQL and up to 20 rows of the result, and asks for a 1-2 sentence explanation using only those numbers.
2. **`app.py`** (a minimal local web server) and **`index.html`** (the page). The **Run** button stays disabled until you write your prediction. There is also a "write the SQL myself" mode with no AI.

## How to use it
```bash
python3 ../06-sql-ventas/cargar_bd.py   # only if ventas.db doesn't exist
cp .env.example .env                    # then put your Gemini API key in .env
python3 app.py
```
Open `http://localhost:8008`. The `.env` file is in `.gitignore`, so the key never reaches GitHub.

## What happened when I tested it
- **The AI made a mistake.** For "does the best-selling month have a higher return rate than the rest?", Gemini wrote SQL that asked for a column called `unidades` from a temporary table where it had been renamed `total_unidades`. SQLite refused to run it. I found the bug by reading the query.
- **Building it step by step.** I wanted to know the best month and how much more it sold than the others. I built the query in 3 steps, predicting each result first: December is the best month (€19,196.02 excluding returns) and sold **273%** more than February, the worst.
- **Exam: 3 queries written by me, without AI.**
  1. Sales lines per product: 5 rows (prediction correct).
  2. Revenue per currency excluding returns: EUR first, then USD and GBP (prediction correct).
  3. Size with the highest return rate in Q4 (October-December): **M, 10.3%**. On the way I learned that filtering with `WHERE devuelto = 1` gives a misleading 100%, because it removes the lines that weren't returned before calculating the percentage.

## Why I built it this way
- **The problem:** it lets you get data out of the database without having to calculate it yourself.
- **Why not just upload the data to an AI chat:** this way is more convenient, safer, protects the information better, and lays foundations you can expand later instead of tearing everything down and starting again when you want to grow.
- **Why the prediction step:** I did it this way to build my own judgement. It also lets you understand what the AI understood from your instructions.
- **What I would change for a real company:** I would add an AI chat that first organises the ideas behind what the company wants to know, before writing the SQL.

## What I learned
- I've more or less learned to understand SQL: I can read a query and fix it, although I don't yet feel able to write one from scratch on my own.
- **The AI is only as precise as the question:** a vague question gets SQL that answers something else.
- **SQL written by AI can look right and still fail**, so a person should review it before trusting the numbers.
- **For things that must always come out the same, use a fixed rule, not AI:** I asked Gemini to format the SQL and it ignored me, so the program formats it instead. It checks that the formatted SQL has exactly the same pieces as the original, and in the queries I tested the result was identical.
