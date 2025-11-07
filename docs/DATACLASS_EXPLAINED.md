# Python Dataclass Explained

## What is `@dataclass`?

`@dataclass` is a **built-in Python decorator** from the `dataclasses` module (Python 3.7+). It's part of Python's standard library - no installation needed!

It automatically generates common methods for classes, saving you from writing boilerplate code.

---

## Standard Python Class vs Dataclass

### Regular Python Class (Without Dataclass)

```python
class Person:
    def __init__(self, name: str, age: int, email: str):
        self.name = name
        self.age = age
        self.email = email
    
    def __repr__(self):
        return f"Person(name='{self.name}', age={self.age}, email='{self.email}')"
    
    def __eq__(self, other):
        if not isinstance(other, Person):
            return False
        return (self.name == other.name and 
                self.age == other.age and 
                self.email == other.email)

# Usage
person1 = Person("John", 30, "john@example.com")
person2 = Person("John", 30, "john@example.com")
print(person1)  # Person(name='John', age=30, email='john@example.com')
print(person1 == person2)  # True
```

**Problems:**
- Lots of boilerplate code
- Have to write `__init__`, `__repr__`, `__eq__` manually
- Easy to make mistakes
- Repetitive

### With Dataclass (Same Functionality, Less Code)

```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int
    email: str

# Usage - EXACTLY the same!
person1 = Person("John", 30, "john@example.com")
person2 = Person("John", 30, "john@example.com")
print(person1)  # Person(name='John', age=30, email='john@example.com')
print(person1 == person2)  # True
```

**Benefits:**
- Much less code!
- `@dataclass` automatically generates:
  - `__init__()` method
  - `__repr__()` method (for nice string representation)
  - `__eq__()` method (for comparing objects)
- Type hints are required (good practice)
- Less error-prone

---

## What Dataclass Generates Automatically

When you use `@dataclass`, Python automatically creates these methods:

### 1. `__init__()` - Constructor

```python
@dataclass
class Person:
    name: str
    age: int

# This is automatically generated:
# def __init__(self, name: str, age: int):
#     self.name = name
#     self.age = age

person = Person("John", 30)  # Works automatically!
```

### 2. `__repr__()` - String Representation

```python
@dataclass
class Person:
    name: str
    age: int

person = Person("John", 30)
print(person)  # Person(name='John', age=30)
# This is automatically generated!
```

### 3. `__eq__()` - Equality Comparison

```python
@dataclass
class Person:
    name: str
    age: int

person1 = Person("John", 30)
person2 = Person("John", 30)
person3 = Person("Jane", 25)

print(person1 == person2)  # True (automatically compares all fields)
print(person1 == person3)  # False
# This is automatically generated!
```

---

## Dataclass Features

### Default Values

```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int = 0  # Default value
    email: str = ""  # Default value

person1 = Person("John")  # age=0, email="" by default
person2 = Person("Jane", 25)  # email="" by default
person3 = Person("Bob", 30, "bob@example.com")  # All fields provided
```

### Optional Fields

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Person:
    name: str
    age: Optional[int] = None  # Can be None
    email: Optional[str] = None

person = Person("John")  # age=None, email=None
```

### Adding Custom Methods

```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int
    
    def is_adult(self) -> bool:
        """Custom method - you can still add your own!"""
        return self.age >= 18

person = Person("John", 20)
print(person.is_adult())  # True
```

### Custom Validation with `__post_init__`

```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int
    
    def __post_init__(self):
        """Runs after __init__ - perfect for validation!"""
        if self.age < 0:
            raise ValueError("Age cannot be negative")
        if not self.name.strip():
            raise ValueError("Name cannot be empty")

# This will raise an error:
# person = Person("", -5)  # ValueError: Name cannot be empty
```

**This is exactly what we use in our `PropertyListingInput`!**

---

## Our Project: How We Use Dataclass

### In `listing_models.py`:

```python
from dataclasses import dataclass
from typing import Literal, Optional

@dataclass
class PropertyListingInput:
    address: str
    listing_type: Literal["sale", "rent"]
    price: float
    notes: str
    billing_cycle: Optional[str] = None
    # ... more fields
    
    def __post_init__(self):
        """Validation after initialization"""
        if not self.address or not self.address.strip():
            raise ValueError("address cannot be empty")
        if self.price <= 0:
            raise ValueError("price must be positive")
        # ... more validation
```

**What this gives us:**
1. ✅ Clean class definition (no boilerplate)
2. ✅ Automatic `__init__`, `__repr__`, `__eq__`
3. ✅ Type hints (for IDE support)
4. ✅ Custom validation in `__post_init__`
5. ✅ No external dependencies (built into Python)

---

## Dataclass vs Regular Class vs Pydantic

### Regular Class
```python
class Person:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
    # ... lots of boilerplate
```
- ✅ Built-in
- ❌ Lots of code
- ❌ No automatic validation

### Dataclass
```python
@dataclass
class Person:
    name: str
    age: int
    # ... minimal code
```
- ✅ Built-in
- ✅ Minimal code
- ✅ Can add validation in `__post_init__`
- ✅ Type hints

### Pydantic
```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int
    # ... minimal code + automatic validation
```
- ❌ Requires installation
- ✅ Minimal code
- ✅ Automatic validation
- ✅ Rich error messages
- ✅ Serialization features

---

## When to Use Each?

### Use Regular Class When:
- You need complete control
- You have complex initialization logic
- You don't need the auto-generated methods

### Use Dataclass When:
- ✅ You want clean, simple data classes
- ✅ You need type hints
- ✅ You want automatic `__init__`, `__repr__`, `__eq__`
- ✅ You can add validation in `__post_init__`
- ✅ You want built-in (no dependencies)

**This is why we use it for boundary models!**

### Use Pydantic When:
- You need automatic validation
- You're building APIs (FastAPI)
- You need serialization (JSON, etc.)
- You want rich error messages

---

## Summary

**`@dataclass` is:**
- ✅ Built into Python (standard library, Python 3.7+)
- ✅ A decorator that generates boilerplate code
- ✅ Not something I created - it's standard Python!
- ✅ Perfect for simple data classes with validation

**In our project:**
- We use `@dataclass` for boundary models (`PropertyListingInput`, `ListingOutput`)
- It gives us clean code + validation + no dependencies
- It's the right tool for the job!

---

## Quick Reference

```python
from dataclasses import dataclass

@dataclass
class MyClass:
    field1: str
    field2: int = 0  # Default value
    
    def __post_init__(self):
        # Custom validation
        if self.field2 < 0:
            raise ValueError("field2 must be non-negative")
```

That's it! Simple, clean, and built into Python.

