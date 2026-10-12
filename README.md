# Fair AI-Based Dispatch System

> **A fairness-aware delivery workload allocation prototype that aims to
> balance the effort assigned to delivery drivers---not just the number
> of packages.**

## Overview

In last-mile delivery, assigning the same number of packages to every
driver does not necessarily create an equal workload. A route with
lightweight packages and easy access can be much easier than a route
with heavy parcels, stairs, difficult parking, traffic, and long
distances.

The **Fair AI-Based Dispatch System** explores how delivery routes can
be evaluated using multiple workload factors and assigned with the goal
of improving fairness across drivers. The current prototype is built
around assumptions and simulated/sample data; the next step is to
validate its assumptions using real-world operational insights and, if
available, anonymized industry data.

## Problem Statement

Traditional dispatch approaches can focus heavily on package count,
distance, or delivery time. These measures alone may overlook the
physical and operational effort required to complete a route.

The goal of this project is to design a dispatch approach that considers
route difficulty and drivers' recent workload history when allocating
delivery work.

## Proposed Solution

The prototype models route effort across multiple dimensions and uses an
assignment optimization step to find a suitable route-to-driver
allocation.

Factors considered in the project include:

-   **Package workload:** package weight, size/volume, and the
    proportion of heavy or bulky parcels.
-   **Building access:** floor-related effort, elevator availability,
    and estimated stair workload.
-   **Route difficulty:** distance, number of stops, stop density,
    traffic, and parking difficulty.
-   **Recent workload:** a driver's previous workload is carried forward
    with configurable decay factors, so older work can have less
    influence than recent work.

The exact availability and quality of these features depend on the input
data. Some values in the current prototype are assumptions or proxies
rather than verified operational measurements.

## How It Works

``` text
Delivery stop, route and package data
                 |
                 v
       Feature extraction
                 |
                 v
       Route clustering
                 |
                 v
     Route workload / effort
                 |
                 v
  Driver's recent workload history
                 |
                 v
       Assignment optimization
                 |
                 v
      Driver-to-route allocation
                 |
                 v
       Review and evaluation
```

### 1. Feature extraction

Raw route and package information is converted into numerical features
that represent physical, access-related, and operational workload.

### 2. Route clustering

Clustering methods such as K-Means or DBSCAN have been explored to
organize delivery stops into manageable groups. The appropriate method
and cluster configuration depend on the data and operational
constraints.

### 3. Workload history

The prototype uses configurable decay factors for workload dimensions,
including physical load, stair load, traffic stress, route distance, and
cognitive/stop-density load. These factors are tunable assumptions and
need calibration against real operational evidence.

### 4. Assignment optimization

The project uses the linear assignment approach available through
`scipy.optimize.linear_sum_assignment` to support route-to-driver
allocation. The intended objective is to reduce unfair workload
distribution, while respecting the cost/effort values supplied to the
assignment step.

**Important:** the quality of the result depends on how route effort and
assignment costs are defined. An optimizer cannot make the allocation
fair if the input features or objective do not represent operational
fairness well.

## Current Scope

The current work focuses on the **algorithmic workload-allocation
component** and a frontend for interacting with the prototype.

-   Route and package feature modelling
-   Workload dimensions for route difficulty
-   Route clustering experiments
-   Historical workload decay
-   Optimization-based assignment
-   Frontend/backend project structure

This is a research and development prototype, not a production-ready
dispatch platform. Features and outputs should be interpreted in the
context of the current implementation and its assumptions.

## Technology

The project has used or explored the following technologies in its
development:

-   **Python** for data processing and algorithmic logic
-   **NumPy / pandas** for numerical and tabular data processing
-   **scikit-learn** for clustering and feature preprocessing
-   **SciPy** for linear assignment optimization
-   **Frontend:** see the `frontend` directory for the current UI
    implementation
-   **Backend:** see the `Backend` directory for the current backend
    implementation

The exact dependencies and startup commands should be taken from the
dependency/configuration files in each directory.

## Getting Started

Clone the repository:

``` bash
git clone https://github.com/Mohammedkalif/fairAiDispatchSystem.git
cd fairAiDispatchSystem
```

Then inspect the project-specific setup files:

-   `Backend/` --- follow its `README`, dependency file, or package
    configuration if present.
-   `frontend/` --- follow its `README` and package configuration if
    present.

Install dependencies and start each component using the commands
specified by those files. Startup commands are intentionally not
hard-coded here because the repository's nested configuration files have
not been verified for this README draft.

## Assumptions and Limitations

-   Current experiments use assumed or simulated inputs; they do not
    establish real-world operational performance.
-   Some workload indicators, such as parking difficulty, traffic
    stress, and stair load, may be estimated proxies.
-   Decay factors and feature weights require calibration with
    operational experts and suitable data.
-   Fairness must be evaluated across drivers and over time---not
    inferred from one assignment or from package counts alone.
-   Clustering quality and workload-allocation quality are different:
    good clusters do not automatically guarantee fair assignments.
-   Real deployment would require operational constraints such as driver
    capacity, shift duration, vehicle limits, delivery time windows, and
    route feasibility to be represented explicitly where relevant.

## Validation Plan

The next stage is to improve the prototype using domain knowledge and,
if permission is granted, anonymized operational data. Useful validation
areas include:

1.  Confirm which factors dispatch teams use to estimate route
    difficulty.
2.  Check whether the required fields are recorded consistently.
3.  Compare the prototype's workload estimates with dispatcher or driver
    assessments.
4.  Evaluate workload balance across multiple drivers and multiple days.
5.  Compare against simple baselines, such as equal stop counts or
    distance-only assignment.
6.  Test operational constraints and document cases where the model's
    allocation is unsuitable.

No real-world improvement or fairness gain is claimed until it has been
measured against an appropriate baseline.

## Future Work

-   Validate workload factors and assumptions with delivery-industry
    experts.
-   Replace synthetic assumptions with authorized, anonymized data where
    available.
-   Calibrate workload weights and history-decay parameters.
-   Define and report fairness metrics alongside operational metrics.
-   Add constraint handling and stronger route-feasibility checks.
-   Improve the UI for comparing assignments and explaining why a route
    was allocated.

## Author

**Mohammed Kalif T**

GitHub: [@Mohammedkalif](https://github.com/Mohammedkalif)

Repository:
[fairAiDispatchSystem](https://github.com/Mohammedkalif/fairAiDispatchSystem)

------------------------------------------------------------------------

