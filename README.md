# online__mart_project
# Project Assignment: Online Afsheen Mart API Using Event-Driven Microservices Architecture
# Project Overview
<p>This project made by Afsheen ,aims to develop an online mart API using an event-driven microservices architecture.
  The API will leverage various technologies such as FastAPI, Docker,  PostgreSQL, Kafka, Protocol Buffers (Protobuf).
  The goal is to create a scalable, maintainable, and efficient system that handles high volumes of transactions and data in a distributed manner.
</p>

# Objectives
<li> Develop a scalable and efficient API for an online mart using microservices.</li>
<li> Implement an event-driven architecture to handle asynchronous communication between services.</li>
<li> Utilize modern technologies such as FastAPI for API development, Docker for containerization, and Kafka for event streaming.</li>
<li> Ensure smooth development and deployment using  Docker Compose.</li>
<li> Use Protocol Buffers (Protobuf) for efficient data serialization.</li>
<li>Persist data using PostgreSQL.</li>

# Technologies
<b>FastAPI:</b> A modern, fast (high-performance) web framework for building APIs with Python.<br>
<b>Docker: </b> For containerizing the microservices, ensuring consistency across different environments.<br>
<b>Docker Compose:</b> For orchestrating multi-container Docker applications.<br>
<b>PostgreSQL:</b> A powerful, open-source relational database system.<br>
<b>SQLModel:</b> For interacting with the PostgreSQL database using Python.<br>
<b>Kafka:</b> A distributed event streaming platform for building real-time data pipelines and streaming applications.<br>
<b>Protocol Buffers (Protobuf):</b> A method developed by Google for serializing structured data, similar to XML or JSON but smaller, faster, and simpler.
<br>
<b>Poetry:</b> Dependency management and packaging for Python.
# Architecture
# Microservices
**User Service:** Manages user authentication, registration, and profiles.<br>
Navigate to http://127.0.0.1:8006 to use this service.<br><br>
**Product Service:** Manages product catalog, including CRUD operations for products.<br>
Navigate to http://127.0.0.1:8005 to use this service.<br><br>
**Order Service:** Handles order creation, updating, and tracking.<br>
Navigate to http://127.0.0.1:8008 to use this service.<br><br>
I**nventory Service:** Manages stock levels and inventory updates.<br>
Navigate to http://127.0.0.1:8007 to use this service.<br><br>
**Notification Service:** Sends notifications (email, SMS) to users about order statuses and other updates.(mailtrap)<br>
Navigate to http://127.0.0.1:8009 to use this service.<br><br>
**Payment Service:** Processes payments and manages transaction records.<br>
Navigate to http://127.0.0.1:8002 to use this service.<br><br>
Note: We will use Pay Fast for Local Payment System. https://gopayfast.com/ And Stripe for international payments.<br><br>
**Kafka UI**<br>
Navigate to http://localhost:8080 

# Event-Driven Communication 
<b>Kafka:</b> Acts as the event bus, facilitating communication between microservices. Each service can produce and consume messages (events) such as user registration, order placement, and inventory updates.
<br>
<b>Protobuf:</b> Used for defining the structure of messages exchanged between services, ensuring efficient and compact serialization.<br>
**Data Storage** <br>
**PostgreSQL:** Each microservice with data persistence needs will have its own PostgreSQL database instance, following the database-per-service pattern.
# Development Environment
**Docker Compose:** Orchestrates the various microservices and dependencies (PostgreSQL, Kafka,etc) during development and testing.<br>
<br>
# Conclusion
<p>This project focuses on developing a robust, scalable, and efficient online mart API utilizing an event-driven microservices architecture. 
  By integrating modern technologies such as FastAPI, Docker, Kafka, Protobuf the system is designed to deliver high performance and 
  maintainability, capable of supporting large-scale operations. The development process will follow a phased approach, emphasizing thorough 
  testing, quality assurance, and continuous improvement throughout the lifecycle of the project.</p>
  <br><br>
To start the project, use the following command:

docker compose up -d




