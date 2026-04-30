---
type: course
progress: ""
tags:
  - course
---
# Course: Developing and Deploying AI/ML Applications on Red Hat OpenShift AI (AI267)

**Course Link:** https://role.rhu.redhat.com/rol-rhu/app/courses/ai267-2.25/
**Course Hub:** https://training-lms.redhat.com/lmt/clmsCurrentLearning.prMain?in_sessionid=39980392421003J0
**Progress:** 0% - Just Started

## Overview

Red Hat OpenShift AI is a platform for generative and predictive AI, based on the upstream Open Data Hub project. Core capabilities:
- Inference
- Training
- Tuning
- GenAIOps

## Course Structure


## Notes

### Key Features of Red Hat OpenShift AI

**Workbenches**
- Containerized, cloud-native working environments
- Run as OpenShift pods

**Data Science Pipelines**
- Automate common ML workflows:
  - Data gathering
  - Training
  - Evaluation
  - Deployment

**Model Serving**
- Deploy pretrained models
- Expose models via REST or gRPC APIs
- Uses KServe as the model serving runtime
- Also supports OpenVINO and vLLM

**Model Registry/Catalog**
- Centralized model management

**Distribution of Workloads**
- Scalable workload distribution

**Metrics and Monitoring**
- Track and monitor model performance

### RHOAI Architecture

RHOAI is organized in two layers:

**Service Layer**
- Handles all the core features:
  - Pipelines
  - Workbenches
  - Model serving
  - Data science workflows

**Management Layer**
- Meta-operator that enables/disables features
- Doesn't handle the features directly, just turns them on
- Orchestrates the service layer components

### Operator Architecture

When you install the Red Hat OpenShift AI Operator, three projects are created:

**redhat-ods-operator**
- Contains the Red Hat OpenShift AI Operator
- Meta-operator that deploys and maintains all components and sub-operators

**redhat-ods-applications**
- Includes the RHOAI dashboard
- Contains other required components of OpenShift AI

**rhods-notebooks**
- Default project for RHOAI workbenches
- Where basic workbenches are deployed when not associated with any user project

### Managing Data Science Projects

Data science projects are the preferred way to organize resources when working on an AI application.

- Similar to a namespace in OpenShift
- Holds the different deployed resources for an AI application

**Components a data science project can include:**
- Workbenches
- Cluster storage
- Connections
- Pipelines
- Models and model servers

**Additional OpenShift resources:**
- Since it's just an OpenShift project, it can also include:
  - ConfigMaps
  - Secrets
  - Services

## Key Takeaways


## Resources & References


## Practice/Exercises

