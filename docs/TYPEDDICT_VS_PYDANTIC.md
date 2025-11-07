# TypedDict vs Pydantic: Understanding the Difference

## Quick Summary

- **TypedDict**: A type hint for dictionaries. No runtime validation. Just tells Python "this dict should have these keys with these types."
- **Pydantic**: A full validation library. Creates classes with automatic validation, serialization, and error handling.

---

## TypedDict Explained

### What is TypedDict?

TypedDict is a **type annotation tool** from Python's `typing` module. It's like a blueprint that tells Python (and your IDE) what keys and types a dictionary should have, but it doesn't actually validate or enforce anything at runtime.

### Example: TypedDict

```python
from typing import TypedDict

class PersonState(TypedDict, total=False):
    name: str
    age: int
    email: str

# Usage - it's just a regular dictionary!
person: PersonState = {
    "name": "John",
    "age": 30,
    "email": "john@example.com"
}

# TypedDict doesn't validate - this won't raise an error at runtime:
person_bad: PersonState = {
    "name": "John",
    "age": "thirty"  # Wrong type, but TypedDict doesn't catch this!
}
```

### Key Characteristics of TypedDict:

1. **No Runtime Validation**: It's just a type hint. Python doesn't check if data matches.
2. **Just a Dictionary**: At runtime, it's a regular Python `dict`.
3. **IDE Support**: Your IDE (like VS Code) will autocomplete keys and show type hints.
4. **Lightweight**: No dependencies, built into Python.
5. **Mutable**: You can add/remove keys freely.

---

## Pydantic Explained

### What is Pydantic?

Pydantic is a **validation library** that creates classes with automatic data validation, serialization, and error handling. It actually checks your data at runtime and raises errors if something is wrong.

### Example: Pydantic

```python
from pydantic import BaseModel, ValidationError

class PersonState(BaseModel):
    name: str
    age: int
    email: str

# Usage - it's a class instance, not a dict!
person = PersonState(
    name="John",
    age=30,
    email="john@example.com"
)

# Pydantic validates - this WILL raise an error:
try:
    person_bad = PersonState(
        name="John",
        age="thirty"  # Pydantic catches this and raises ValidationError!
    )
except ValidationError as e:
    print(e)  # Shows detailed validation errors
```

### Key Characteristics of Pydantic:

1. **Runtime Validation**: Actually checks data and raises errors if invalid.
2. **Class Instance**: Creates objects, not dictionaries (though you can convert to dict).
3. **Rich Error Messages**: Tells you exactly what's wrong.
4. **Serialization**: Easy conversion to/from JSON, dict, etc.
5. **Immutable by Default**: Can't change fields after creation (unless configured otherwise).
6. **External Dependency**: Requires installing `pydantic` package.

---

## Side-by-Side Comparison

### Example 1: Creating an Object

**TypedDict:**
```python
from typing import TypedDict

class State(TypedDict, total=False):
    name: str
    age: int

# It's just a dict
state: State = {"name": "John", "age": 30}
print(type(state))  # <class 'dict'>
```

**Pydantic:**
```python
from pydantic import BaseModel

class State(BaseModel):
    name: str
    age: int

# It's a class instance
state = State(name="John", age=30)
print(type(state))  # <class '__main__.State'>
print(state.dict())  # Convert to dict: {'name': 'John', 'age': 30}
```

### Example 2: Validation

**TypedDict:**
```python
# No validation - this won't error!
state: State = {"name": "John", "age": "thirty"}  # Wrong type, but no error
```

**Pydantic:**
```python
# Validation - this WILL error!
try:
    state = State(name="John", age="thirty")  # Raises ValidationError
except ValidationError as e:
    print(e)
    # Output: 1 validation error for State
    # age
    #   value is not a valid integer (type=type_error.integer)
```

### Example 3: Accessing Data

**TypedDict:**
```python
# Dict-style access
state: State = {"name": "John", "age": 30}
print(state["name"])  # "John"
print(state.get("name"))  # "John"
```

**Pydantic:**
```python
# Attribute-style access (or dict-style)
state = State(name="John", age=30)
print(state.name)  # "John" (attribute access)
print(state["name"])  # "John" (dict-style also works)
print(state.dict()["name"])  # "John" (convert to dict first)
```

---

## Why TypedDict for LangGraph State?

### LangGraph's Design Philosophy

LangGraph is designed to work with **dictionaries** that flow between nodes. Each node:
1. Receives a dictionary (state)
2. Reads from it
3. Updates it
4. Returns the updated dictionary

### Example: LangGraph Node

```python
def my_node(state: PropertyListingState) -> PropertyListingState:
    # Read from state (dict-style)
    address = state["address"]
    
    # Update state (dict-style)
    state["normalized_address"] = address.upper()
    
    # Return updated state
    return state
```

### Why TypedDict Works Better Here:

1. **Native Dict Operations**: LangGraph nodes work with dicts naturally.
2. **Mutable**: Nodes need to update state, which is easier with dicts.
3. **Lightweight**: No extra validation overhead (validation happens in nodes).
4. **LangGraph Standard**: LangGraph documentation and examples use TypedDict.
5. **Flexible**: Easy to add/remove fields as state flows through nodes.

### If We Used Pydantic Instead:

```python
# Would need to convert back and forth
def my_node(state: PropertyListingState) -> PropertyListingState:
    # Convert to dict to work with it
    state_dict = state.dict()
    
    # Do work
    state_dict["normalized_address"] = state_dict["address"].upper()
    
    # Convert back to Pydantic model
    return PropertyListingState(**state_dict)
```

This is more cumbersome and less efficient.

---

## When to Use Each?

### Use TypedDict When:

✅ You need type hints for dictionaries  
✅ Working with frameworks that expect dicts (like LangGraph)  
✅ You want lightweight, no-dependency solution  
✅ You're doing validation elsewhere (in your nodes/functions)  
✅ You need mutable, flexible data structures  

### Use Pydantic When:

✅ You need automatic validation  
✅ You're building APIs (FastAPI uses Pydantic)  
✅ You need serialization/deserialization (JSON, etc.)  
✅ You want rich error messages  
✅ You're working with external data (user input, API responses)  
✅ You want immutable, validated objects  

---

## In Our Project

### We Use TypedDict For:

- **LangGraph State** (`PropertyListingState`): Flows between nodes, needs to be mutable dict

### We Use Pydantic/Dataclasses For:

- **Boundary Models** (`PropertyListingInput`, `ListingOutput`): User-facing data that needs validation

Actually, we're using `@dataclass` for boundary models, which is similar to Pydantic but built into Python. It gives us:
- Type hints
- Some validation (via `__post_init__`)
- Clean class structure
- No external dependencies

---

## Summary Table

| Feature | TypedDict | Pydantic |
|---------|-----------|----------|
| **Type** | Type hint for dict | Validation library |
| **Runtime Validation** | ❌ No | ✅ Yes |
| **What You Get** | Regular dict | Class instance |
| **Dependencies** | None (built-in) | Requires `pydantic` |
| **Mutable** | ✅ Yes | ⚠️ Configurable |
| **IDE Support** | ✅ Yes | ✅ Yes |
| **Error Messages** | ❌ None | ✅ Rich & detailed |
| **Best For** | Type hints, LangGraph | Validation, APIs |

---

## Real-World Analogy

**TypedDict** is like a **blueprint**:
- Shows what a house should look like
- Doesn't enforce anything
- Just a guide for builders (developers)

**Pydantic** is like a **building inspector**:
- Actually checks if the house meets standards
- Rejects it if something's wrong
- Gives detailed reports on what needs fixing

---

## Conclusion

For LangGraph state, **TypedDict is the right choice** because:
1. LangGraph works with dictionaries
2. Nodes need to mutate state easily
3. It's the standard in LangGraph
4. Validation happens in nodes, not in the state itself

For boundary models (input/output), we use **dataclasses** because:
1. We need validation at the boundaries
2. Clean class structure
3. No external dependencies needed

