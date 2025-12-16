# SQL Injection Patterns

SQL injection occurs when untrusted data is concatenated or interpolated into SQL queries without proper sanitization or parameterization.

## CWE Reference

**CWE-89**: Improper Neutralization of Special Elements used in an SQL Command ('SQL Injection')

## Vulnerability Pattern

```
User Input → String Concatenation/Interpolation → SQL Execution = SQL Injection
```

## Key Components

### 1. SQL Sinks (Dangerous Functions)

Functions that execute SQL queries:

**Ruby/Rails:**
- `ActiveRecord::Base.connection.execute`
- `ActiveRecord::Base.connection.exec_query`
- `ActiveRecord::Base.connection.select_all`
- `Model.find_by_sql`
- Raw SQL in `where` clauses: `Model.where("...")`

**Java/JDBC:**
- `Statement.execute`
- `Statement.executeQuery`
- `Statement.executeUpdate`
- `Connection.prepareStatement` (when building dynamic SQL)

**JavaScript/Node:**
- `db.query()`
- `connection.execute()`
- `knex.raw()`
- Raw SQL in ORMs

**Python:**
- `cursor.execute()`
- `cursor.executemany()`
- Raw SQL in Django: `Model.objects.raw()`
- SQLAlchemy: `session.execute(text(...))`

### 2. Tainted Sources (User Input)

Common sources of untrusted data:

- HTTP parameters: `params[:id]`, `request.query`, `req.params.id`
- Form data: `request.form`, `req.body`
- Headers: `request.headers`, `req.headers`
- Cookies: `request.cookies`, `req.cookies`
- URL paths: `request.path`, `req.path`

### 3. Sanitizers (Safe Patterns)

Properly parameterized queries:

**Ruby/Rails:**
```ruby
# ✅ SAFE - Parameterized
Model.where("name = ?", params[:name])
Model.where(name: params[:name])

# ❌ UNSAFE - String interpolation
Model.where("name = '#{params[:name]}'")
```

**Java:**
```java
// ✅ SAFE - Prepared statement
PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
ps.setString(1, userId);

// ❌ UNSAFE - String concatenation
Statement stmt = conn.createStatement();
stmt.executeQuery("SELECT * FROM users WHERE id = '" + userId + "'");
```

**JavaScript:**
```javascript
// ✅ SAFE - Parameterized
db.query('SELECT * FROM users WHERE id = ?', [userId])

// ❌ UNSAFE - String concatenation
db.query('SELECT * FROM users WHERE id = ' + userId)
```

**Python:**
```python
# ✅ SAFE - Parameterized
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# ❌ UNSAFE - String formatting
cursor.execute("SELECT * FROM users WHERE id = " + user_id)
```

## Bearer Rule Examples

### Ruby SQL Injection

```yaml
languages: [ruby]
severity: high
metadata:
  description: "Detects SQL injection from unsanitized user input in Rails"
  cwe_id: "89"
patterns:
  - pattern: |
      $<MODEL>.where($<SQL>)
    filters:
      - variable: SQL
        detection: sql_injection
  - pattern: |
      $<OBJ>.execute($<SQL>)
    filters:
      - variable: SQL
        detection: sql_injection
auxiliary:
  sql_injection:
    patterns:
      - pattern: |
          "$<BEFORE>#{$<USER_INPUT>}$<AFTER>"
      - pattern: |
          $<SQL> + $<USER_INPUT>
  user_input:
    patterns:
      - pattern: params
      - pattern: request
message: "Possible SQL injection: user input is concatenated into SQL query. Use parameterized queries instead."
```

### Java SQL Injection

```yaml
languages: [java]
severity: high
metadata:
  description: "Detects SQL injection from string concatenation in JDBC"
  cwe_id: "89"
patterns:
  - pattern: |
      $<STMT>.execute($<SQL>)
    filters:
      - variable: STMT
        detection: statement_type
      - variable: SQL
        detection: concatenated_sql
  - pattern: |
      $<STMT>.executeQuery($<SQL>)
    filters:
      - variable: STMT
        detection: statement_type
      - variable: SQL
        detection: concatenated_sql
auxiliary:
  statement_type:
    patterns:
      - pattern: Statement
      - pattern: PreparedStatement
  concatenated_sql:
    patterns:
      - pattern: |
          $<LEFT> + $<RIGHT>
      - pattern: |
          String.format($<...>)
message: "Possible SQL injection: use PreparedStatement with parameter binding instead of string concatenation"
```

### JavaScript SQL Injection

```yaml
languages: [javascript]
severity: high
metadata:
  description: "Detects SQL injection in Node.js database queries"
  cwe_id: "89"
patterns:
  - pattern: |
      $<DB>.$<METHOD>($<SQL>)
    filters:
      - variable: METHOD
        detection: sql_methods
      - variable: SQL
        detection: string_concat
auxiliary:
  sql_methods:
    patterns:
      - pattern: query
      - pattern: execute
      - pattern: run
  string_concat:
    patterns:
      - pattern: |
          $<LEFT> + $<RIGHT>
      - pattern: |
          `$<BEFORE>${$<VAR>}$<AFTER>`
message: "Possible SQL injection: use parameterized queries with placeholders instead of string concatenation"
```

### Python SQL Injection

```yaml
languages: [python]
severity: high
metadata:
  description: "Detects SQL injection in Python database code"
  cwe_id: "89"
patterns:
  - pattern: |
      $<CURSOR>.execute($<SQL>)
    filters:
      - variable: SQL
        detection: unsafe_sql
  - pattern: |
      $<CURSOR>.executemany($<SQL>, $<...>)
    filters:
      - variable: SQL
        detection: unsafe_sql
auxiliary:
  unsafe_sql:
    patterns:
      - pattern: |
          $<LEFT> + $<RIGHT>
      - pattern: |
          f"$<BEFORE>{$<VAR>}$<AFTER>"
      - pattern: |
          "$<STR>" % $<VAR>
      - pattern: |
          "$<STR>".format($<...>)
message: "Possible SQL injection: use parameterized queries with %s placeholders instead of string formatting"
```

## ORM-Specific Patterns

### Rails ActiveRecord

```ruby
# ❌ UNSAFE patterns
User.where("email = '#{params[:email]}'")
User.find_by_sql("SELECT * FROM users WHERE id = #{id}")
ActiveRecord::Base.connection.execute("DELETE FROM #{table}")

# ✅ SAFE patterns
User.where("email = ?", params[:email])
User.where(email: params[:email])
User.find_by_sql(["SELECT * FROM users WHERE id = ?", id])
```

### Spring/JPA

```java
// ❌ UNSAFE patterns
entityManager.createQuery("FROM User WHERE name = '" + userName + "'")
Query query = session.createQuery("FROM User WHERE id = " + userId)

// ✅ SAFE patterns
TypedQuery<User> query = entityManager.createQuery(
    "FROM User WHERE name = :name", User.class)
    .setParameter("name", userName);
```

### Sequelize (Node.js)

```javascript
// ❌ UNSAFE patterns
sequelize.query(`SELECT * FROM users WHERE id = ${userId}`)
sequelize.query("SELECT * FROM users WHERE name = '" + userName + "'")

// ✅ SAFE patterns
sequelize.query('SELECT * FROM users WHERE id = ?', { 
    replacements: [userId] 
})
```

## Testing SQL Injection Rules

### Test Cases to Include

1. **Direct concatenation**: `query + user_input`
2. **String interpolation**: `"SELECT * FROM #{table}"`
3. **Template literals**: `` `SELECT * WHERE id = ${id}` ``
4. **Format strings**: `"SELECT * WHERE id = %s" % (user_id)`
5. **Multiple inputs**: Concatenating multiple user inputs
6. **Indirect flow**: User input assigned to variable first

### Expected Detections (BAD)

```ruby
# Should detect
execute("SELECT * FROM users WHERE id = #{params[:id]}")
query = "SELECT * FROM " + table_name
User.where("email = '#{email}'")
```

### Expected Safe Patterns (GOOD)

```ruby
# Should NOT detect
User.where("email = ?", email)
User.where(email: email)
execute("SELECT * FROM users WHERE id = ?", [id])
```

## Common False Positives

1. **Static strings**: `execute("SELECT * FROM users")` - No user input
2. **Constants**: `TABLE_NAME = "users"` then `"FROM #{TABLE_NAME}"` - Not user input
3. **Sanitized input**: Input that's been validated/sanitized before use

## Framework-Specific Considerations

### Rails
- Check for `sanitize_sql` usage (safe)
- Consider Arel usage (generally safe)
- Watch for `find_by_sql` with interpolation

### Spring
- `@Query` annotations with SpEL can be vulnerable
- JPA Criteria API is generally safe
- Named parameters (`:param`) are safe

### Express/Sequelize
- Sequelize ORM methods are generally safe
- `sequelize.query()` with replacements is safe
- Raw queries need scrutiny

### Django
- ORM queries are generally safe
- `.raw()` and `.extra()` need attention
- `cursor.execute()` needs parameterization

## References

- OWASP SQL Injection: https://owasp.org/www-community/attacks/SQL_Injection
- CWE-89: https://cwe.mitre.org/data/definitions/89.html
- Rails Security Guide: https://guides.rubyonrails.org/security.html#sql-injection
- JDBC Security: https://docs.oracle.com/javase/tutorial/jdbc/basics/prepared.html
