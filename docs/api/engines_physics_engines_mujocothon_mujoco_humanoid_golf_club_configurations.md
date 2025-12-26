# engines.physics_engines.mujocothon.mujoco_humanoid_golf.club_configurations

Golf club configuration database.

Provides realistic club specifications for different club types.

## Classes

### ClubSpecification

Specification for a golf club.

### ClubDatabase

Database of golf club specifications.

#### Methods

##### get_club
```python
def get_club(cls: Any, club_id: str) -> Any
```

Get club specification by ID.

Args:
    club_id: Club identifier (e.g., 'driver', '7_iron')

Returns:
    ClubSpecification or None if not found

##### get_all_clubs
```python
def get_all_clubs(cls: Any) -> dict[Any]
```

Get all club specifications.

Returns:
    Dictionary mapping club ID to specification

##### get_clubs_by_type
```python
def get_clubs_by_type(cls: Any, club_type: str) -> list[ClubSpecification]
```

Get all clubs of a specific type.

Args:
    club_type: Club type (Driver, Wood, Iron, Wedge, Putter)

Returns:
    List of matching ClubSpecifications

##### get_club_types
```python
def get_club_types(cls: Any) -> list[str]
```

Get list of all club types.

Returns:
    List of unique club types

##### compute_total_mass
```python
def compute_total_mass(cls: Any, spec: ClubSpecification) -> float
```

Compute total club mass.

Args:
    spec: Club specification

Returns:
    Total mass in grams

##### compute_total_mass_kg
```python
def compute_total_mass_kg(cls: Any, spec: ClubSpecification) -> float
```

Compute total club mass in kg.

Args:
    spec: Club specification

Returns:
    Total mass in kilograms

##### length_to_meters
```python
def length_to_meters(cls: Any, length_inches: float) -> float
```

Convert club length to meters.

Args:
    length_inches: Length in inches

Returns:
    Length in meters

##### export_to_json
```python
def export_to_json(cls: Any, output_path: str) -> None
```

Export club database to JSON file.

Args:
    output_path: Output JSON file path

##### create_custom_club
```python
def create_custom_club(cls: Any, name: str, club_type: str) -> ClubSpecification
```

Create a custom club specification.

Args:
    name: Club name
    club_type: Club type
    **kwargs: Additional specification parameters

Returns:
    ClubSpecification

## Constants

- `CLUBS`
