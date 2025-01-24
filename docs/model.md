# What are models

A model if the definition of what is stored in the database.
It specify attributes, their types, as well as some display options.

# Defining models
To define a model you should inherit from AModel 
and specify a META_MODEL attribute to store a 
unique identifier for this model.

Specifying the IS_ABSTRACT attribute with a True value prevent
the UI from directly instantiating this model.

```python
from core.models.a_model import AModel

class MyModel(AModel):
    META_MODEL = "my_model"
    
    property: str
```

