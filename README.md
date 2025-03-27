# Pet Grooming Service Website

A full-stack web application for booking pet grooming services using Django for the backend and HTML/CSS/JavaScript for the frontend.
This project was built to allow pet owners to easily schedule and manage grooming appointments.

## Features

**User Authentication** – Secure login and registration for customers and admins
**Appointment Booking System** – Customers can submit booking requests, while admins manage approvals
**Admin Dashboard** – Admins can view, modify, and cancel bookings
**Service Management** – Admins can create, update, and remove grooming services
**Responsive UI** – Works on desktop and mobile devices

## Technologies Used

- **Backend:** Django, Python
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite

## Screenshots

**Customer View**:
[Screenshot 2025-03-27 233404](https://github.com/user-attachments/assets/eb0fd905-ae61-4b7b-b1cf-158c0b85a749)
![Screenshot 2025-03-27 233522](https://github.com/user-attachments/assets/ba4220fe-b03b-4d71-b353-953cc45e6008)
![Screenshot 2025-03-27 233717](https://github.com/user-attachments/assets/d34251e4-3986-4f73-af6c-90e327ea7900)

**Admin View**:
![Screenshot 2025-03-27 234121](https://github.com/user-attachments/assets/20a7d3b3-3997-4d6b-b2ce-5402d87f2352)
![Screenshot 2025-03-27 234312](https://github.com/user-attachments/assets/c00f744a-c9b6-4f16-a47d-d6b549e8fb1c)
![Screenshot 2025-03-27 234226](https://github.com/user-attachments/assets/a389e0a2-ca40-436c-b6eb-7f432668cc9b)



## Installation & Run Locally

1. **Clone the Repository**
   git clone https://github.com/y1nghui/pet_grooming_service_website.git
   cd pet_grooming_service_website

2. **Create a Virtual Environment & Install Dependencies**
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
4. **Run Migrations & Start the Server**
   python manage.py migrate
   python manage.py runserver

5. **Access the Website**
   Open `http://127.0.0.1:8000/` in your browser



