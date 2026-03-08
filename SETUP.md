# README Marker Placement

Add the following two lines to your `README.md` wherever you want the
Apple Books section to appear — for example, near the bottom of your profile:

```markdown
## 📚 Reading

<!-- BOOKS:START -->
<!-- BOOKS:END -->
```

The GitHub Action will automatically fill in everything between the markers
every day. The rendered output will look like:

---

## 📚 Reading

### 📖 Currently Reading

| Book | Author | Progress |
|------|--------|----------|
| **The Pragmatic Programmer** | David Thomas | `████████░░` 80% |
| **Atomic Habits** | James Clear | `████░░░░░░` 40% |

### ✅ Recently Finished

| Book | Author |
|------|--------|
| **Clean Code** | Robert C. Martin |
| **The Lean Startup** | Eric Ries |

**2** finished &nbsp;·&nbsp; **2** in progress &nbsp;·&nbsp; **12** total in library

<sub>Last updated: March 08, 2026</sub>

---

## Setup Checklist

1. **Register a self-hosted runner** on your Mac
   → Repo Settings → Actions → Runners → New self-hosted runner → macOS

2. **Install the library** on your Mac:
   ```bash
   pip install py_apple_books
   ```

3. **Copy the scripts** to the root of your repo:
   - `fetch_books.py`
   - `update_readme.py`

4. **Copy the workflow** to your repo:
   ```
   .github/workflows/update-books.yml
   ```

5. **Add the markers** to your `README.md` (see above)

6. **Enable write permissions** for GitHub Actions:
   → Repo Settings → Actions → General → Workflow permissions → Read and write

7. **Start your runner** on your Mac and trigger the workflow manually once to test:
   → Actions tab → "Update Apple Books Stats" → Run workflow
