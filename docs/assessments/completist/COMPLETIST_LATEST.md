<<<<<<< HEAD
# Completist Report: 2026-03-26

## Executive Summary
- **Critical Gaps**: 349
- **Feature Gaps (TRACKED_TASK)**: 36
- **Technical Debt**: 18
- **Documentation Gaps**: 280
=======
# Completist Report: 2026-04-23

## Executive Summary
- **Critical Gaps**: 242
- **Feature Gaps (TRACKED_TASK)**: 2
- **Technical Debt**: 27
- **Documentation Gaps**: 765
>>>>>>> origin/main

## Visualization
### Status Overview
```mermaid
pie title Completion Status
<<<<<<< HEAD
    "Impl Gaps (Critical)" : 349
    "Feature Requests (TRACKED_TASK)" : 36
    "Technical Debt (TRACKED_DEFECT)" : 18
    "Doc Gaps" : 280
=======
    "Impl Gaps (Critical)" : 242
    "Feature Requests (TRACKED_TASK)" : 2
    "Technical Debt (TRACKED_DEFECT)" : 27
    "Doc Gaps" : 765
>>>>>>> origin/main
```

### Top Impacted Modules
```mermaid
pie title Issues by Module
<<<<<<< HEAD
    "src" : 365
    "shared" : 14
    "scripts" : 11
    "tests" : 10
    "reports" : 2
=======
    "src" : 199
    "vendor" : 60
    "scripts" : 4
    ".gaai" : 4
    "tests" : 3
>>>>>>> origin/main
```

## Critical Incomplete (Top 50)
| File | Line | Type | Impact | Coverage | Complexity |
|---|---|---|---|---|---|
<<<<<<< HEAD
| `./src/api/auth/security.py` | 328 | Stub | 5 | 2 | 4 |
| `./src/shared/python/physics/topography.py` | 92 | Stub | 5 | 3 | 4 |
| `./src/shared/python/physics/topography.py` | 103 | Stub | 5 | 3 | 4 |
| `./src/shared/python/physics/topography.py` | 115 | Stub | 5 | 3 | 4 |
| `./src/shared/python/physics/terrain_mixin.py` | 35 | Stub | 5 | 3 | 4 |
| `./src/shared/python/physics/flexible_shaft.py` | 318 | Stub | 5 | 3 | 4 |
| `./src/shared/python/physics/flexible_shaft.py` | 322 | Stub | 5 | 3 | 4 |
| `./src/shared/python/physics/flexible_shaft.py` | 326 | Stub | 5 | 3 | 4 |
| `./src/shared/python/physics/flexible_shaft.py` | 335 | Stub | 5 | 3 | 4 |
| `./src/shared/python/physics/flexible_shaft.py` | 365 | Stub | 5 | 3 | 4 |
=======
| `./src/api/auth/security.py` | 339 | Stub | 5 | 2 | 4 |
| `./src/shared/python/physics/flexible_shaft.py` | 325 | Stub | 5 | 3 | 4 |
| `./src/shared/python/physics/flexible_shaft.py` | 329 | Stub | 5 | 3 | 4 |
| `./src/shared/python/physics/flexible_shaft.py` | 333 | Stub | 5 | 3 | 4 |
| `./src/shared/python/physics/flexible_shaft.py` | 342 | Stub | 5 | 3 | 4 |
| `./src/shared/python/physics/flexible_shaft.py` | 372 | Stub | 5 | 3 | 4 |
>>>>>>> origin/main
| `./src/shared/python/physics/flight_models.py` | 162 | Stub | 5 | 3 | 4 |
| `./src/shared/python/physics/flight_models.py` | 168 | Stub | 5 | 3 | 4 |
| `./src/shared/python/physics/flight_models.py` | 174 | Stub | 5 | 3 | 4 |
| `./src/shared/python/physics/flight_models.py` | 179 | Stub | 5 | 3 | 4 |
<<<<<<< HEAD
| `./src/shared/python/physics/terrain_engine.py` | 43 | Stub | 5 | 3 | 4 |
| `./src/shared/python/physics/impact_model.py` | 135 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/perturbation_analysis.py` | 32 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/perturbation_analysis.py` | 38 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/controls_widget_base.py` | 418 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/controls_widget_base.py` | 428 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/controls_widget_base.py` | 438 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/controls_widget_base.py` | 448 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/controls_widget_base.py` | 479 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/simulation_panel.py` | 84 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/simulation_panel.py` | 85 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/simulation_panel.py` | 86 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/matrix_widget_base.py` | 144 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/matrix_widget_base.py` | 154 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/matrix_widget_base.py` | 169 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/matrix_widget_base.py` | 179 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/base_pendulum_widget.py` | 111 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/base_pendulum_widget.py` | 116 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/base_pendulum_widget.py` | 121 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/base_pendulum_widget.py` | 126 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/base_pendulum_widget.py` | 131 | Stub | 5 | 3 | 4 |
=======
| `./src/shared/python/physics/impact_model/models.py` | 20 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/controls_widget_base.py` | 429 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/controls_widget_base.py` | 439 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/controls_widget_base.py` | 449 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/controls_widget_base.py` | 459 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/matrix_widget_base.py` | 148 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/matrix_widget_base.py` | 158 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/matrix_widget_base.py` | 173 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/matrix_widget_base.py` | 183 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/base_pendulum_widget.py` | 115 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/base_pendulum_widget.py` | 120 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/base_pendulum_widget.py` | 125 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/base_pendulum_widget.py` | 130 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pendulum_simulator/gui/base_pendulum_widget.py` | 135 | Stub | 5 | 3 | 4 |
>>>>>>> origin/main
| `./src/shared/python/model_generation/plugins/__init__.py` | 21 | Stub | 5 | 3 | 4 |
| `./src/shared/python/model_generation/plugins/__init__.py` | 27 | Stub | 5 | 3 | 4 |
| `./src/shared/python/model_generation/plugins/__init__.py` | 32 | Stub | 5 | 3 | 4 |
| `./src/shared/python/model_generation/plugins/__init__.py` | 36 | Stub | 5 | 3 | 4 |
| `./src/shared/python/model_generation/library/repository.py` | 44 | Stub | 5 | 3 | 4 |
| `./src/shared/python/model_generation/library/repository.py` | 50 | Stub | 5 | 3 | 4 |
| `./src/shared/python/model_generation/library/repository.py` | 55 | Stub | 5 | 3 | 4 |
| `./src/shared/python/model_generation/library/repository.py` | 60 | Stub | 5 | 3 | 4 |
| `./src/shared/python/model_generation/editor/editor_clipboard.py` | 41 | Stub | 5 | 3 | 4 |
| `./src/shared/python/model_generation/editor/editor_modifications.py` | 53 | Stub | 5 | 3 | 4 |
| `./src/shared/python/model_generation/editor/editor_modifications.py` | 55 | Stub | 5 | 3 | 4 |
<<<<<<< HEAD
| `./src/shared/python/model_generation/builders/base_builder.py` | 191 | Stub | 5 | 3 | 4 |
| `./src/shared/python/model_generation/builders/base_builder.py` | 201 | Stub | 5 | 3 | 4 |
=======
| `./src/shared/python/model_generation/editor/editor_modifications.py` | 57 | Stub | 5 | 3 | 4 |
| `./src/shared/python/model_generation/editor/editor_modifications.py` | 59 | Stub | 5 | 3 | 4 |
| `./src/shared/python/model_generation/builders/base_builder.py` | 191 | Stub | 5 | 3 | 4 |
| `./src/shared/python/model_generation/builders/base_builder.py` | 201 | Stub | 5 | 3 | 4 |
| `./src/shared/python/humanoid_character_builder/generators/mesh_generator_models.py` | 59 | Stub | 5 | 3 | 4 |
| `./src/shared/python/humanoid_character_builder/generators/mesh_generator_models.py` | 65 | Stub | 5 | 3 | 4 |
| `./src/shared/python/humanoid_character_builder/generators/mesh_generator_models.py` | 70 | Stub | 5 | 3 | 4 |
| `./src/shared/python/humanoid_character_builder/generators/mesh_generator_models.py` | 90 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pose_estimation/interface.py` | 24 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pose_estimation/interface.py` | 32 | Stub | 5 | 3 | 4 |
| `./src/shared/python/pose_estimation/interface.py` | 43 | Stub | 5 | 3 | 4 |
| `./src/shared/python/perturbation/analyzer_base.py` | 100 | Stub | 5 | 3 | 4 |
| `./src/shared/python/perturbation/analyzer_base.py` | 104 | Stub | 5 | 3 | 4 |
| `./src/shared/python/perturbation/analyzer_base.py` | 108 | Stub | 5 | 3 | 4 |
| `./src/shared/python/calc_backend/protocols.py` | 35 | Stub | 5 | 3 | 4 |
>>>>>>> origin/main

## Feature Gap Matrix
| Module | Feature Gap | Type |
|---|---|---|
<<<<<<< HEAD
| `./src/shared/models/opensim/opensim-models/CMakeLists.txt` | RENAME run_forward.xml) # TRACKED_TASK inconsistent filename; which should we use? | TRACKED_TASK |
| `./src/shared/models/opensim/opensim-models/CMakeLists.txt` | # TRACKED_TASK subject01_metabolics* files? | TRACKED_TASK |
| `./src/shared/models/opensim/opensim-models/CMakeLists.txt` | # TRACKED_TASK should we copy over the OutputReference folder? | TRACKED_TASK |
| `./src/shared/models/opensim/opensim-models/CMakeLists.txt` | PATTERN "addPrescribedMotion.py" EXCLUDE # TRACKED_TASK leave in or not? | TRACKED_TASK |
| `./src/shared/tools/human-gazebo/legacy/control/src/HumanGazeboControlModule.cpp` | //TRACKED_TASK read the joint names list and then put then in the control board options | TRACKED_TASK |
| `./src/engines/pendulum_models/tools/matlab_utilities/README.md` | - TRACKED_TASK, TRACKED_DEFECT, HACK, XXX placeholders | TRACKED_TASK |
| `./src/engines/physics_engines/drake/tools/matlab_utilities/README.md` | - TRACKED_TASK, TRACKED_DEFECT, HACK, XXX placeholders | TRACKED_TASK |
| `./src/engines/physics_engines/pinocchio/tools/matlab_utilities/README.md` | - TRACKED_TASK, TRACKED_DEFECT, HACK, XXX placeholders | TRACKED_TASK |
| `./src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab_utilities/README.md` | - TRACKED_TASK, TRACKED_DEFECT, HACK, XXX placeholders | TRACKED_TASK |
| `./shared/models/opensim/opensim-models/Tutorials/Building_a_Passive_Dynamic_Walker/DynamicWalkerBuild/DynamicWalkerBuildModelStudent.cpp` | // TRACKED_TASK: Add Code to Begin Model here | TRACKED_TASK |
| `./shared/models/opensim/opensim-models/Tutorials/Building_a_Passive_Dynamic_Walker/DynamicWalkerBuild/DynamicWalkerBuildModelStudent.cpp` | // TRACKED_TASK: Set the coordinate properties | TRACKED_TASK |
| `./shared/models/opensim/opensim-models/Tutorials/Building_a_Passive_Dynamic_Walker/skeleton.cpp` | // TRACKED_TASK: Add Code to Begin Model here | TRACKED_TASK |
| `./shared/models/opensim/opensim-models/Tutorials/Building_a_Passive_Dynamic_Walker/DynamicWalkerBuildModel.cpp` | // Section A.1 TRACKED_TASK: Create the Pelvis and set the coordinate properties | TRACKED_TASK |
| `./shared/models/opensim/opensim-models/Tutorials/Building_a_Passive_Dynamic_Walker/DynamicWalkerBuildModel.cpp` | // Section A.2 TRACKED_TASK: Create the LeftThigh, LeftShank, RightThigh and RightShank bodies | TRACKED_TASK |
| `./shared/models/opensim/opensim-models/Tutorials/Building_a_Passive_Dynamic_Walker/DynamicWalkerBuildModel.cpp` | // Section B.1 TRACKED_TASK: Add ContactSphere to the left hip, the knee, and the foot points | TRACKED_TASK |
| `./shared/models/opensim/opensim-models/Tutorials/Building_a_Passive_Dynamic_Walker/DynamicWalkerBuildModel.cpp` | // Section B.2 TRACKED_TASK: Add HuntCrossleyForces | TRACKED_TASK |
| `./shared/models/opensim/opensim-models/Tutorials/Building_a_Passive_Dynamic_Walker/DynamicWalkerBuildModel.cpp` | // Section B.2 TRACKED_TASK: Add HuntCrossleyForces betweeen the remaining ContactSpheres | TRACKED_TASK |
| `./shared/models/opensim/opensim-models/Tutorials/Building_a_Passive_Dynamic_Walker/DynamicWalkerBuildModel.cpp` | // Section C.1 TRACKED_TASK: Construct CoordinateLimitForces for the Hip and Knee | TRACKED_TASK |
| `./shared/models/opensim/opensim-models/CMakeLists.txt` | RENAME run_forward.xml) # TRACKED_TASK inconsistent filename; which should we use? | TRACKED_TASK |
| `./shared/models/opensim/opensim-models/CMakeLists.txt` | # TRACKED_TASK subject01_metabolics* files? | TRACKED_TASK |
| `./shared/models/opensim/opensim-models/CMakeLists.txt` | # TRACKED_TASK should we copy over the OutputReference folder? | TRACKED_TASK |
| `./shared/models/opensim/opensim-models/CMakeLists.txt` | PATTERN "addPrescribedMotion.py" EXCLUDE # TRACKED_TASK leave in or not? | TRACKED_TASK |
| `./scripts/refresh_completist_data.py` | "TRACKED_TASK\|TRACKED_DEFECT\|XXX\|HACK\|TEMP", | TRACKED_TASK |
| `./scripts/generate_todo_fixme_register.py` | ["rg", "-n", "TRACKED_TASK\|TRACKED_DEFECT", "src", "tests", "scripts"], | TRACKED_TASK |
| `./scripts/generate_todo_fixme_register.py` | "# TRACKED_TASK/TRACKED_DEFECT Debt Register", | TRACKED_TASK |
| `./scripts/generate_todo_fixme_register.py` | "This register is generated from inline TRACKED_TASK/TRACKED_DEFECT markers.", | TRACKED_TASK |
| `./scripts/generate_todo_fixme_register.py` | marker = "TRACKED_TASK" if "TRACKED_TASK" in text else "TRACKED_DEFECT" | TRACKED_TASK |
| `./scripts/pragmatic_programmer_review.py` | """Report high TRACKED_TASK counts as a technical debt indicator.""" | TRACKED_TASK |
| `./scripts/pragmatic_programmer_review.py` | if "TRACKED_TASK" in content: | TRACKED_TASK |
| `./scripts/pragmatic_programmer_review.py` | "title": f"High TRACKED_TASK count ({len(todos)})", | TRACKED_TASK |
| `./CLAUDE.md` | 5. No TRACKED_TASK/TRACKED_DEFECT unless tied to a tracked GitHub issue | TRACKED_TASK |
| `./tests/tools/test_code_quality_check.py` | lines = ["# TRACKED_TASK: fix this", "def test():", "    ...  ", "    pass"] | TRACKED_TASK |
| `./tests/tools/test_code_quality_check.py` | assert any("TRACKED_TASK placeholder" in t for t in types) | TRACKED_TASK |
| `./tests/tools/test_code_quality_check.py` | lines = ["# TRACKED_TASK: internal marker"] | TRACKED_TASK |
| `./tests/tools/test_code_quality_check.py` | f.write_text("# TRACKED_TASK: fix this\n") | TRACKED_TASK |
| `./tests/tools/test_code_quality_check.py` | assert any("TRACKED_TASK" in i[1] for i in issues) | TRACKED_TASK |
=======
| `./vendor/ud-tools/src/tools/matlab_quality_utils.py` | """Check for TODO, FIXME, HACK, XXX, and placeholders.""" | TRACKED_TASK |
| `./vendor/ud-tools/src/tools/matlab_utilities/README.md` | - TODO, FIXME, HACK, XXX placeholders | TRACKED_TASK |
>>>>>>> origin/main

## Technical Debt Register
| File | Line | Issue | Type |
|---|---|---|---|
| `./src/api/utils/error_codes.py` | 53 | # General Errors (GMS-GEN-XXX) | XXX |
| `./src/api/utils/error_codes.py` | 59 | # Engine Errors (GMS-ENG-XXX) | XXX |
| `./src/api/utils/error_codes.py` | 67 | # Simulation Errors (GMS-SIM-XXX) | XXX |
| `./src/api/utils/error_codes.py` | 76 | # Video Errors (GMS-VID-XXX) | XXX |
| `./src/api/utils/error_codes.py` | 83 | # Analysis Errors (GMS-ANL-XXX) | XXX |
| `./src/api/utils/error_codes.py` | 88 | # Auth Errors (GMS-AUT-XXX) | XXX |
| `./src/api/utils/error_codes.py` | 95 | # Validation Errors (GMS-VAL-XXX) | XXX |
| `./src/api/utils/error_codes.py` | 101 | # Resource Errors (GMS-RES-XXX) | XXX |
| `./src/api/utils/error_codes.py` | 106 | # System Errors (GMS-SYS-XXX) | XXX |
| `./src/shared/models/opensim/opensim-models/Tutorials/doc/styles/site.css` | 3404 | html body { /* HACK: Temporary fix for CONF-15412 */ | HACK |
| `./src/engines/pendulum_models/tools/matlab_utilities/README.md` | 261 | - TRACKED_TASK, TRACKED_DEFECT, HACK, XXX placeholders | XXX |
| `./src/engines/physics_engines/drake/tools/matlab_utilities/README.md` | 261 | - TRACKED_TASK, TRACKED_DEFECT, HACK, XXX placeholders | XXX |
| `./src/engines/physics_engines/pinocchio/tools/matlab_utilities/README.md` | 261 | - TRACKED_TASK, TRACKED_DEFECT, HACK, XXX placeholders | XXX |
| `./src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab_utilities/README.md` | 261 | - TRACKED_TASK, TRACKED_DEFECT, HACK, XXX placeholders | XXX |
| `./src/tools/matlab_utilities/scripts/matlab_quality_check.py` | 83 | (r"\bHACK\b", "HACK comment found"), | HACK |
| `./src/tools/matlab_utilities/scripts/matlab_quality_check.py` | 84 | (r"\bXXX\b", "XXX comment found"), | XXX |
| `./shared/models/opensim/opensim-models/Tutorials/doc/styles/site.css` | 3404 | html body { /* HACK: Temporary fix for CONF-15412 */ | HACK |
| `./scripts/refresh_completist_data.py` | 60 | "TRACKED_TASK\|TRACKED_DEFECT\|XXX\|HACK\|TEMP", | XXX |
| `./vendor/ud-tools/src/tools/matlab_quality_utils.py` | 321 | (r"\bHACK\b", "HACK comment found"), | HACK |
| `./vendor/ud-tools/src/tools/matlab_quality_utils.py` | 322 | (r"\bXXX\b", "XXX comment found"), | XXX |
| `./.gaai/core/skills/cross/friction-retrospective/SKILL.md` | 58 | - `signal: high` → automatic promotion candidate (CAND-XXX) | XXX |
| `./.gaai/core/skills/cross/friction-retrospective/SKILL.md` | 64 | - **High-Signal Events (CAND-XXX):** each candidate with evidence, proposed promotion target, and re | XXX |
| `./.gaai/core/skills/cross/friction-retrospective/SKILL.md` | 91 | - Promotion candidates (CAND-XXX) with evidence and recommended targets | XXX |
| `./.gaai/core/skills/cross/friction-retrospective/SKILL.md` | 98 | - Every CAND-XXX has at least 2 supporting evidence entries (or 1 with `signal: high`) | XXX |
| `./tests/unit/api/test_error_codes.py` | 36 | """Postcondition: All codes follow GMS-XXX-NNN format.""" | XXX |
| `./tests/unit/utils/test_error_codes.py` | 39 | """Every error code must follow GMS-XXX-NNN pattern.""" | XXX |
| `./tests/unit/utils/test_error_codes.py` | 42 | assert len(parts) == 3, f"{code.name} doesn't follow GMS-XXX-NNN" | XXX |
<<<<<<< HEAD
| `./tests/tools/test_code_quality_check.py` | 83 | lines = ["# TRACKED_DEFECT: broken logic"] | TRACKED_DEFECT |
| `./tests/tools/test_code_quality_check.py` | 85 | assert any("TRACKED_DEFECT" in i[1] for i in issues) | TRACKED_DEFECT |
=======
>>>>>>> origin/main

## Recommended Implementation Order
Prioritized by Impact (High) and Complexity (Low).
| Priority | File | Issue | Metrics (I/C/C) |
|---|---|---|---|
<<<<<<< HEAD
| 1 | `./src/engines/pendulum_models/tools/matlab_utilities/README.md` | - TRACKED_TASK, TRACKED_DEFECT, HACK, XXX placeholders | 5/2/3 |
| 2 | `./src/engines/physics_engines/drake/tools/matlab_utilities/README.md` | - TRACKED_TASK, TRACKED_DEFECT, HACK, XXX placeholders | 5/2/3 |
| 3 | `./src/engines/physics_engines/pinocchio/tools/matlab_utilities/README.md` | - TRACKED_TASK, TRACKED_DEFECT, HACK, XXX placeholders | 5/2/3 |
| 4 | `./src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab_utilities/README.md` | - TRACKED_TASK, TRACKED_DEFECT, HACK, XXX placeholders | 5/2/3 |
| 5 | `./src/api/auth/security.py` | __init__ | 5/2/4 |
| 6 | `./src/shared/python/physics/topography.py` | get_elevation_at | 5/3/4 |
| 7 | `./src/shared/python/physics/topography.py` | get_gradient_at | 5/3/4 |
| 8 | `./src/shared/python/physics/topography.py` | bounds | 5/3/4 |
| 9 | `./src/shared/python/physics/terrain_mixin.py` | get_position | 5/3/4 |
| 10 | `./src/shared/python/physics/flexible_shaft.py` | initialize | 5/3/4 |
| 11 | `./src/shared/python/physics/flexible_shaft.py` | get_state | 5/3/4 |
| 12 | `./src/shared/python/physics/flexible_shaft.py` | apply_load | 5/3/4 |
| 13 | `./src/shared/python/physics/flexible_shaft.py` | step | 5/3/4 |
| 14 | `./src/shared/python/physics/flexible_shaft.py` | apply_load | 5/3/4 |
| 15 | `./src/shared/python/physics/flight_models.py` | name | 5/3/4 |
| 16 | `./src/shared/python/physics/flight_models.py` | description | 5/3/4 |
| 17 | `./src/shared/python/physics/flight_models.py` | reference | 5/3/4 |
| 18 | `./src/shared/python/physics/flight_models.py` | simulate | 5/3/4 |
| 19 | `./src/shared/python/physics/terrain_engine.py` | set_ground_properties | 5/3/4 |
| 20 | `./src/shared/python/physics/impact_model.py` | solve | 5/3/4 |

## Issues Created
- Created `docs/assessments/issues/Issue_2144_Incomplete_Stub_in_security_py_328.md`
- Created `docs/assessments/issues/Issue_2028_Incomplete_Stub_in_topography_py_92.md`
- Created `docs/assessments/issues/Issue_2029_Incomplete_Stub_in_topography_py_103.md`
- Created `docs/assessments/issues/Issue_2030_Incomplete_Stub_in_topography_py_115.md`
- Created `docs/assessments/issues/Issue_2031_Incomplete_Stub_in_terrain_mixin_py_35.md`
- Created `docs/assessments/issues/Issue_2149_Incomplete_Stub_in_flexible_shaft_py_318.md`
- Created `docs/assessments/issues/Issue_2150_Incomplete_Stub_in_flexible_shaft_py_322.md`
- Created `docs/assessments/issues/Issue_2151_Incomplete_Stub_in_flexible_shaft_py_326.md`
- Created `docs/assessments/issues/Issue_2152_Incomplete_Stub_in_flexible_shaft_py_335.md`
- Created `docs/assessments/issues/Issue_2153_Incomplete_Stub_in_flexible_shaft_py_365.md`
- Created `docs/assessments/issues/Issue_2088_Incomplete_Stub_in_flight_models_py_162.md`
- Created `docs/assessments/issues/Issue_2089_Incomplete_Stub_in_flight_models_py_168.md`
- Created `docs/assessments/issues/Issue_2090_Incomplete_Stub_in_flight_models_py_174.md`
- Created `docs/assessments/issues/Issue_2091_Incomplete_Stub_in_flight_models_py_179.md`
- Created `docs/assessments/issues/Issue_2041_Incomplete_Stub_in_terrain_engine_py_43.md`
- Created `docs/assessments/issues/Issue_2159_Incomplete_Stub_in_impact_model_py_135.md`
- Created `docs/assessments/issues/Issue_2125_Incomplete_Stub_in_perturbation_analysis_py_32.md`
- Created `docs/assessments/issues/Issue_2126_Incomplete_Stub_in_perturbation_analysis_py_38.md`
- Created `docs/assessments/issues/Issue_2127_Incomplete_Stub_in_controls_widget_base_py_418.md`
- Created `docs/assessments/issues/Issue_2128_Incomplete_Stub_in_controls_widget_base_py_428.md`
- Created `docs/assessments/issues/Issue_2129_Incomplete_Stub_in_controls_widget_base_py_438.md`
- Created `docs/assessments/issues/Issue_2130_Incomplete_Stub_in_controls_widget_base_py_448.md`
- Created `docs/assessments/issues/Issue_2131_Incomplete_Stub_in_controls_widget_base_py_479.md`
- Created `docs/assessments/issues/Issue_2133_Incomplete_Stub_in_simulation_panel_py_84.md`
- Created `docs/assessments/issues/Issue_2134_Incomplete_Stub_in_simulation_panel_py_85.md`
- Created `docs/assessments/issues/Issue_2169_Incomplete_Stub_in_simulation_panel_py_86.md`
- Created `docs/assessments/issues/Issue_2135_Incomplete_Stub_in_matrix_widget_base_py_144.md`
- Created `docs/assessments/issues/Issue_2136_Incomplete_Stub_in_matrix_widget_base_py_154.md`
- Created `docs/assessments/issues/Issue_2137_Incomplete_Stub_in_matrix_widget_base_py_169.md`
- Created `docs/assessments/issues/Issue_2138_Incomplete_Stub_in_matrix_widget_base_py_179.md`
- Created `docs/assessments/issues/Issue_2139_Incomplete_Stub_in_base_pendulum_widget_py_111.md`
- Created `docs/assessments/issues/Issue_2140_Incomplete_Stub_in_base_pendulum_widget_py_116.md`
- Created `docs/assessments/issues/Issue_2141_Incomplete_Stub_in_base_pendulum_widget_py_121.md`
- Created `docs/assessments/issues/Issue_2142_Incomplete_Stub_in_base_pendulum_widget_py_126.md`
- Created `docs/assessments/issues/Issue_2143_Incomplete_Stub_in_base_pendulum_widget_py_131.md`
- Created `docs/assessments/issues/Issue_2043_Incomplete_Stub_in___init___py_21.md`
- Created `docs/assessments/issues/Issue_2044_Incomplete_Stub_in___init___py_27.md`
- Created `docs/assessments/issues/Issue_2045_Incomplete_Stub_in___init___py_32.md`
- Created `docs/assessments/issues/Issue_2046_Incomplete_Stub_in___init___py_36.md`
- Created `docs/assessments/issues/Issue_2047_Incomplete_Stub_in_repository_py_44.md`
- Created `docs/assessments/issues/Issue_2048_Incomplete_Stub_in_repository_py_50.md`
- Created `docs/assessments/issues/Issue_2049_Incomplete_Stub_in_repository_py_55.md`
- Created `docs/assessments/issues/Issue_2050_Incomplete_Stub_in_repository_py_60.md`
- Created `docs/assessments/issues/Issue_2051_Incomplete_Stub_in_editor_clipboard_py_41.md`
- Created `docs/assessments/issues/Issue_2052_Incomplete_Stub_in_editor_modifications_py_49.md`
- Created `docs/assessments/issues/Issue_2053_Incomplete_Stub_in_editor_modifications_py_51.md`
- Created `docs/assessments/issues/Issue_2054_Incomplete_Stub_in_editor_modifications_py_53.md`
- Created `docs/assessments/issues/Issue_2055_Incomplete_Stub_in_editor_modifications_py_55.md`
- Created `docs/assessments/issues/Issue_2192_Incomplete_Stub_in_base_builder_py_191.md`
- Created `docs/assessments/issues/Issue_2193_Incomplete_Stub_in_base_builder_py_201.md`
=======
| 1 | `./src/api/auth/security.py` | __init__ | 5/2/4 |
| 2 | `./src/shared/python/physics/flexible_shaft.py` | initialize | 5/3/4 |
| 3 | `./src/shared/python/physics/flexible_shaft.py` | get_state | 5/3/4 |
| 4 | `./src/shared/python/physics/flexible_shaft.py` | apply_load | 5/3/4 |
| 5 | `./src/shared/python/physics/flexible_shaft.py` | step | 5/3/4 |
| 6 | `./src/shared/python/physics/flexible_shaft.py` | apply_load | 5/3/4 |
| 7 | `./src/shared/python/physics/flight_models.py` | name | 5/3/4 |
| 8 | `./src/shared/python/physics/flight_models.py` | description | 5/3/4 |
| 9 | `./src/shared/python/physics/flight_models.py` | reference | 5/3/4 |
| 10 | `./src/shared/python/physics/flight_models.py` | simulate | 5/3/4 |
| 11 | `./src/shared/python/physics/impact_model/models.py` | solve | 5/3/4 |
| 12 | `./src/shared/python/pendulum_simulator/gui/controls_widget_base.py` | _apply_preset | 5/3/4 |
| 13 | `./src/shared/python/pendulum_simulator/gui/controls_widget_base.py` | get_params | 5/3/4 |
| 14 | `./src/shared/python/pendulum_simulator/gui/controls_widget_base.py` | _get_joint_names | 5/3/4 |
| 15 | `./src/shared/python/pendulum_simulator/gui/controls_widget_base.py` | _get_torque_inputs | 5/3/4 |
| 16 | `./src/shared/python/pendulum_simulator/gui/matrix_widget_base.py` | get_matrix_size | 5/3/4 |
| 17 | `./src/shared/python/pendulum_simulator/gui/matrix_widget_base.py` | get_matrix_entries | 5/3/4 |
| 18 | `./src/shared/python/pendulum_simulator/gui/matrix_widget_base.py` | get_column_labels | 5/3/4 |
| 19 | `./src/shared/python/pendulum_simulator/gui/matrix_widget_base.py` | _draw_coupling_ratio | 5/3/4 |
| 20 | `./src/shared/python/pendulum_simulator/gui/base_pendulum_widget.py` | _get_total_length | 5/3/4 |

## Issues Created
- Created `docs/assessments/issues/Issue_2274_Incomplete_Stub_in_security_py_339.md`
- Created `docs/assessments/issues/Issue_2279_Incomplete_Stub_in_flexible_shaft_py_325.md`
- Created `docs/assessments/issues/Issue_2280_Incomplete_Stub_in_flexible_shaft_py_329.md`
- Created `docs/assessments/issues/Issue_2281_Incomplete_Stub_in_flexible_shaft_py_333.md`
- Created `docs/assessments/issues/Issue_2282_Incomplete_Stub_in_flexible_shaft_py_342.md`
- Created `docs/assessments/issues/Issue_2283_Incomplete_Stub_in_flexible_shaft_py_372.md`
- Created `docs/assessments/issues/Issue_2037_Incomplete_Stub_in_flight_models_py_162.md`
- Created `docs/assessments/issues/Issue_2038_Incomplete_Stub_in_flight_models_py_168.md`
- Created `docs/assessments/issues/Issue_2039_Incomplete_Stub_in_flight_models_py_174.md`
- Created `docs/assessments/issues/Issue_2040_Incomplete_Stub_in_flight_models_py_179.md`
- Created `docs/assessments/issues/Issue_2299_Incomplete_Stub_in_models_py_20.md`
- Created `docs/assessments/issues/Issue_2306_Incomplete_Stub_in_controls_widget_base_py_429.md`
- Created `docs/assessments/issues/Issue_2307_Incomplete_Stub_in_controls_widget_base_py_439.md`
- Created `docs/assessments/issues/Issue_2308_Incomplete_Stub_in_controls_widget_base_py_449.md`
- Created `docs/assessments/issues/Issue_2309_Incomplete_Stub_in_controls_widget_base_py_459.md`
- Created `docs/assessments/issues/Issue_2221_Incomplete_Stub_in_matrix_widget_base_py_148.md`
- Created `docs/assessments/issues/Issue_2222_Incomplete_Stub_in_matrix_widget_base_py_158.md`
- Created `docs/assessments/issues/Issue_2223_Incomplete_Stub_in_matrix_widget_base_py_173.md`
- Created `docs/assessments/issues/Issue_2224_Incomplete_Stub_in_matrix_widget_base_py_183.md`
- Created `docs/assessments/issues/Issue_2225_Incomplete_Stub_in_base_pendulum_widget_py_115.md`
- Created `docs/assessments/issues/Issue_2226_Incomplete_Stub_in_base_pendulum_widget_py_120.md`
- Created `docs/assessments/issues/Issue_2227_Incomplete_Stub_in_base_pendulum_widget_py_125.md`
- Created `docs/assessments/issues/Issue_2228_Incomplete_Stub_in_base_pendulum_widget_py_130.md`
- Created `docs/assessments/issues/Issue_2229_Incomplete_Stub_in_base_pendulum_widget_py_135.md`
- Created `docs/assessments/issues/Issue_2062_Incomplete_Stub_in___init___py_21.md`
- Created `docs/assessments/issues/Issue_2063_Incomplete_Stub_in___init___py_27.md`
- Created `docs/assessments/issues/Issue_2064_Incomplete_Stub_in___init___py_32.md`
- Created `docs/assessments/issues/Issue_2065_Incomplete_Stub_in___init___py_36.md`
- Created `docs/assessments/issues/Issue_2066_Incomplete_Stub_in_repository_py_44.md`
- Created `docs/assessments/issues/Issue_2067_Incomplete_Stub_in_repository_py_50.md`
- Created `docs/assessments/issues/Issue_2068_Incomplete_Stub_in_repository_py_55.md`
- Created `docs/assessments/issues/Issue_2069_Incomplete_Stub_in_repository_py_60.md`
- Created `docs/assessments/issues/Issue_2070_Incomplete_Stub_in_editor_clipboard_py_41.md`
- Created `docs/assessments/issues/Issue_2073_Incomplete_Stub_in_editor_modifications_py_53.md`
- Created `docs/assessments/issues/Issue_2074_Incomplete_Stub_in_editor_modifications_py_55.md`
- Created `docs/assessments/issues/Issue_2241_Incomplete_Stub_in_editor_modifications_py_57.md`
- Created `docs/assessments/issues/Issue_2242_Incomplete_Stub_in_editor_modifications_py_59.md`
- Created `docs/assessments/issues/Issue_2192_Incomplete_Stub_in_base_builder_py_191.md`
- Created `docs/assessments/issues/Issue_2193_Incomplete_Stub_in_base_builder_py_201.md`
- Created `docs/assessments/issues/Issue_2349_Incomplete_Stub_in_mesh_generator_models_py_59.md`
- Created `docs/assessments/issues/Issue_2350_Incomplete_Stub_in_mesh_generator_models_py_65.md`
- Created `docs/assessments/issues/Issue_2351_Incomplete_Stub_in_mesh_generator_models_py_70.md`
- Created `docs/assessments/issues/Issue_2352_Incomplete_Stub_in_mesh_generator_models_py_90.md`
- Created `docs/assessments/issues/Issue_2353_Incomplete_Stub_in_interface_py_24.md`
- Created `docs/assessments/issues/Issue_2354_Incomplete_Stub_in_interface_py_32.md`
- Created `docs/assessments/issues/Issue_2355_Incomplete_Stub_in_interface_py_43.md`
- Created `docs/assessments/issues/Issue_2406_Incomplete_Stub_in_analyzer_base_py_100.md`
- Created `docs/assessments/issues/Issue_2407_Incomplete_Stub_in_analyzer_base_py_104.md`
- Created `docs/assessments/issues/Issue_2408_Incomplete_Stub_in_analyzer_base_py_108.md`
- Created `docs/assessments/issues/Issue_2359_Incomplete_Stub_in_protocols_py_35.md`
>>>>>>> origin/main
