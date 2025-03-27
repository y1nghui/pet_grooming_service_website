from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login ,logout
from django.contrib import messages
from django import forms
from .forms import CreateUserForm, UserUpdateForm, OwnerUpdateForm, PetForm, BookingForm
from .models import Pet, Owner, Booking, Room, Feedback
from django.urls import reverse
from django.views.generic.edit import UpdateView
from .forms import BookingForm, EditBookingForm, RoomForm
import datetime
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime



def create_room(request):
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')  
    else:
        form = RoomForm()
    return render(request, 'create_room.html', {'form': form})
    

def AdminPage(request):
    rooms = Room.objects.all()

    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        new_status = request.POST.get('status')
        
        if booking_id and new_status:
            booking = get_object_or_404(Booking, id=booking_id)
            if new_status in ['Ongoing', 'Completed', 'Cancelled']:
                booking.status = new_status
                booking.save()
    
    sort_by = request.GET.get('sort_by', 'date')

    order_by = '-date' 
    if sort_by == 'id':
        order_by = 'id'
    elif sort_by == 'service':
        order_by = 'service'

    ongoing_bookings = Booking.objects.filter(status='Ongoing').order_by(order_by)
    completed_bookings = Booking.objects.filter(status='Completed').order_by(order_by)
    cancelled_bookings = Booking.objects.filter(status='Cancelled').order_by(order_by)

    owners = Owner.objects.all()
    context = {
        'ongoing_bookings': ongoing_bookings,
        'completed_bookings': completed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'owners': owners,
        'rooms': rooms,
    }
    return render(request, 'admin_dashboard.html', context)


class BookingUpdateView(UpdateView):
    model = Booking
    form_class = BookingForm
    template_name = 'edit_booking.html'

    def get_object(self):
        booking_id = self.kwargs.get('pk')
        return get_object_or_404(Booking, id=booking_id)

    def form_valid(self, form):
        form.save()
        return redirect('admin_dashboard')


def BookingPage(request):
    owner = request.user.owner

    if request.method == 'POST':
        form = BookingForm(owner, request.POST, pet_required=True, service_required=True)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.owner = owner

            if booking.service == 'Pet Hotel':
                booking.date = None
                booking.time = None
                # Check room availability only for Pet Hotel
                available_rooms = Room.objects.all()
                for room in available_rooms:
                    overlapping_bookings = Booking.objects.filter(
                        room=room,
                        checkin__lte=booking.checkout,
                        checkout__gte=booking.checkin,
                        service='Pet Hotel' 
                    ).exists()
                    if not overlapping_bookings:
                        booking.room = room
                        break
                else:
                    messages.error(request, "No rooms are available for the selected dates.")
                    context = {'form': form, 'bookings': Booking.objects.filter(owner=owner)}
                    return render(request, 'bookingpage.html', context)
            else:
                booking.checkin = None
                booking.checkout = None

            booking.save()
            form.save_m2m()
            messages.success(request, 'Booking has been updated')
            context = {'form': form, 'booking': booking}
            return render(request, 'bookingpage.html', context)
        else:
            print(form.errors)
    else:
        form = BookingForm(owner, pet_required=True, service_required=True)
    
    bookings = Booking.objects.filter(owner=owner)
    context = {'form': form, 'bookings': bookings}
    return render(request, 'bookingpage.html', context)


def update_times(request):
    service = request.GET.get('service')
    date = request.GET.get('date')
    
    form = BookingForm(request.user.owner, initial={'service': service, 'date': date})
    available_times = form.get_available_time_choices(date, service)
    
    return JsonResponse({'available_times': dict(available_times)})


def edit_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    owner = booking.owner
    owner_pets = Pet.objects.filter(owner=owner)

    if request.method == 'POST':
        form = EditBookingForm(owner, request.POST, instance=booking)
        if form.is_valid():
            booking_instance = form.save(commit=False)
            

            booking_instance.save()
            # messages.success(request, 'Booking has been updated successfully.')
            return redirect('admin_dashboard')  # Redirect to admin dashboard after successful update
        else:
            # Form is not valid, print errors (optional)
            print(form.errors)
    else:
        form = BookingForm(owner, instance=booking)

    return render(request, 'edit_booking.html', {'form': form, 'booking': booking, 'owner_pets': owner_pets})



def ownerpf(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    pets = booking.pet.all()
    print(pets)  # Debug output
    return render(request, 'admin_showprofile.html', {'booking': booking, 'pets': pets})



def timetable(request):
    bookings = Booking.objects.all()
    context = {
        "bookings": bookings,
    }
    return render(request, 'timetable.html', context)



def get_booking(request):
    bookings = Booking.objects.all()  # Retrieve all bookings from the database
    events = []
    for booking in bookings:
        if booking.service == 'Hair Grooming':
            pets = booking.pet.all()  # Fetch all pets associated with this booking
            pet_names = ', '.join([pet.name for pet in pets])

            event = {
                "title": pet_names,
                'service': booking.service,
                "start": f"{booking.date}T{booking.time}",
                "color": "#AFEEEE",
                "id": booking.id,
                'owner': booking.owner.user.username,
                "pet": pet_names
            }
            events.append(event)

        elif booking.service == 'Bath and Dry':
            pets = booking.pet.all()  # Fetch all pets associated with this booking
            pet_names = ', '.join([pet.name for pet in pets])

            event = {
                "title":pet_names,
                'service': booking.service,
                "start": f"{booking.date}T{booking.time}",
                "color": '#87CEFA',
                "id": booking.id,
                'owner': booking.owner.user.username,
                "pet": pet_names

            }
            events.append(event)

        elif booking.service == 'Pet Daycare':
            pets = booking.pet.all()  # Fetch all pets associated with this booking
            pet_names = ', '.join([pet.name for pet in pets])

            if booking.time == 'full_day':
                events.append({
                    'title': f'{pet_names} - fullday',
                    'id' : booking.id,
                    'service' : booking.service,
                    'start': booking.date,
                    'end': booking.date,
                    'owner': booking.owner.user.username,
                    "pet": pet_names,
                    'allDay': True,
                    'color' : '#f0e130',
                })

            elif booking.time == 'morning':
                events.append({
                    'title': f'{pet_names} - morning',
                    'id' : booking.id,
                    'service' : booking.service,
                    'start': booking.date,
                    'end': booking.date,
                    'owner': booking.owner.user.username,
                    "pet": pet_names,
                    'allDay': True,
                    'color' : '#4682B4',
                })

            elif booking.time == 'noon':
                events.append({
                    'title': f'{pet_names} - noon',
                    'id' : booking.id,
                    'service' : booking.service,
                    'start': booking.date,
                    'end': booking.date,              
                    'color' : '#FF6347',
                    'owner': booking.owner.user.username,
                    "pet": pet_names,
                    'allDay': True,
                })

    return JsonResponse(events, safe=False)




def CalendarPage(request):
    owner = request.user.owner
    bookings = Booking.objects.filter(owner=owner, )
    context = {
        "bookings": bookings,
    }
    return render(request, 'calendar.html', context)


def all_bookings(request):
    owner = request.user.owner
    bookings = Booking.objects.filter(owner=owner)
    out = []
    for booking in bookings:
        if booking.service in ['Hair Grooming', 'Bath and Dry','Pet Daycare']:
            if booking.date and booking.time:
                pets = booking.pet.all()  # Fetch all pets associated with this booking
                pet_names = ', '.join([pet.name for pet in pets])
                color = '#FF6347' if booking.service == 'Hair Grooming' else '#4682B4' if booking.service == 'Bath and Dry' else '#f0e130'

                out.append({
                    'title': booking.service,
                    'id': booking.id,
                    'start': booking.date.strftime("%Y-%m-%dT%H:%M:%S"),
                    'allDay': True,
                    'color': color,
                    'details': {
                        'id': booking.id,
                        'Date': booking.date.strftime("%Y-%m-%d"),
                        'Time': booking.time,
                        'Service': booking.service,
                        'Pets': pet_names,
                    }
                })
        elif booking.service in ['Pet Hotel']:
            if booking.checkin and booking.checkout:
                room_data = {
                    'name': booking.room.name,  
                }
                pets = booking.pet.all() 
                pet_names = ', '.join([pet.name for pet in pets])                
                end_date = booking.checkout + timedelta(days=1)  
                out.append({
                    'title': booking.service,
                    'id': booking.id,
                    'start': booking.checkin.strftime("%Y-%m-%dT%H:%M:%S"),
                    'end': end_date.strftime("%Y-%m-%dT%H:%M:%S"),
                    'allDay': True,
                    'color': '#32CD32' ,  
                    'details': {
                        'id': booking.id,
                        'Checkin': booking.checkin.strftime("%Y-%m-%d"),
                        'Checkout': booking.checkout.strftime("%Y-%m-%d"),
                        'Service': booking.service,
                        'Room': room_data,
                        'Pets': pet_names,
                    }
                })

    return JsonResponse(out, safe=False)

def room_detail(request, room_id=None):
    room = get_object_or_404(Room, pk=room_id) if room_id else None
    rooms = Room.objects.all()

    context = {
        'room': room,
        'rooms': rooms,
    }

    return render(request, 'room_detail.html', context)


def get_room_events(request, room_id):
    bookings = Booking.objects.filter(room_id=room_id, service='Pet Hotel')

    events = []
    for booking in bookings:
        start_time = booking.checkin.strftime("%Y-%m-%dT%H:%M:%S") if booking.checkin else None
        end_date = booking.checkout + timedelta(days=1)  
        pets = booking.pet.all()  
        pet_names = ', '.join([pet.name for pet in pets]) 
        room_data = {
            'name': booking.room.name,  
        }

        title = f"Booking ID: {booking.id} - {pet_names}"   
        
        events.append({
            'id': booking.id,
            'title': title,
            'start': start_time,
            'end': end_date.strftime("%Y-%m-%dT%H:%M:%S"),
            'allDay': True,
            'color': '#32CD32',
            'details': {
                'id': booking.id,
                'Checkin': booking.checkin.strftime("%Y-%m-%d"),
                'Checkout': booking.checkout.strftime("%Y-%m-%d"),
                'Room': room_data,
                'Pets': pet_names,
                'Owner' : booking.owner.user.username,
                'ContactNumber' : booking.owner.phone_number
            }


        })

    return JsonResponse(events, safe=False)


@csrf_exempt
def resize_booking(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data.'})

    booking_id = data.get('id')
    new_start_str = data.get('start')
    new_end_str = data.get('end')

    if not booking_id or not new_start_str or not new_end_str:
        return JsonResponse({'status': 'error', 'message': 'Missing required fields.'})

    try:
        booking = get_object_or_404(Booking, id=booking_id)
        if booking.service != 'Pet Hotel':
            return JsonResponse({'status': 'error', 'message': 'Only Pet Hotel bookings can be resized.'})

        new_start = datetime.fromisoformat(new_start_str)
        new_end = datetime.fromisoformat(new_end_str) if new_end_str else None

        if not new_end:
            return JsonResponse({'status': 'error', 'message': 'End date is required for Pet Hotel.'})

        overlapping_bookings = Booking.objects.filter(
            room_id=booking.room_id,
            checkin__lt=new_end,
            checkout__gte=new_start
        ).exclude(id=booking_id)

        if overlapping_bookings.exists():
            return JsonResponse({'status': 'error', 'message': 'The new dates overlap with an existing booking.'})

        booking.checkin = new_start
        booking.checkout = new_end - timedelta(days=1)
        booking.save()

        return JsonResponse({'status': 'success'})
    except ValueError as e:
        return JsonResponse({'status': 'error', 'message': 'Invalid date format.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@csrf_exempt
def update_booking_dates(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data.'})

    booking_id = data.get('id')
    new_start_str = data.get('start')
    new_end_str = data.get('end')

    if not booking_id or not new_start_str or not new_end_str:
        return JsonResponse({'status': 'error', 'message': 'Missing required fields.'})

    try:
        booking = get_object_or_404(Booking, id=booking_id)
        if booking.service != 'Pet Hotel':
            return JsonResponse({'status': 'error', 'message': 'Only Pet Hotel bookings can be updated.'})

        new_start = datetime.fromisoformat(new_start_str)
        new_end = datetime.fromisoformat(new_end_str) if new_end_str else None

        if not new_end:
            return JsonResponse({'status': 'error', 'message': 'End date is required for Pet Hotel.'})

        overlapping_bookings = Booking.objects.filter(
            room_id=booking.room_id,
            checkin__lt=new_end,
            checkout__gte=new_start
        ).exclude(id=booking_id)

        if overlapping_bookings.exists():
            return JsonResponse({'status': 'error', 'message': 'The new dates overlap with an existing booking.'})

        booking.checkin = new_start
        booking.checkout = new_end - timedelta(days=1)
        booking.save()

        return JsonResponse({'status': 'success'})
    except ValueError as e:
        return JsonResponse({'status': 'error', 'message': 'Invalid date format.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
    

def PetprofilePage(request):
    try:
        owner_instance = Owner.objects.get(user=request.user)
    except Owner.DoesNotExist:
        messages.error(request, 'pls create a owner profile first')
        return redirect ('profile')
    pet_instances = Pet.objects.filter(owner=owner_instance)
    if request.method == 'POST':
        form = PetForm(request.POST, request.FILES)
        if form.is_valid():
            pet = form.save(commit=False)
            pet.owner = owner_instance
            pet.save()
            form.save_m2m()

            # form.save()
            messages.success(request, f'profile has been updated')
            return redirect('petprofile')
    else:
        form = PetForm()

    context = {'form':form, 'pet_instances': pet_instances}
    return render(request, 'petprofile.html', context)


def edit_pet(request, pet_id):
    pet_instance = get_object_or_404(Pet, id=pet_id)
    if request.method == 'POST':
        form = PetForm(request.POST, request.FILES, instance=pet_instance)
        if form.is_valid():
            pet = form.save(commit=False)
            pet.save()
            return redirect('edit_pet',pet_id=pet_id)
        
    else:
        form = PetForm(initial={
            'name': pet_instance.name,
            'owner': pet_instance.owner,
            'age': pet_instance.age,
            'species': pet_instance.species,
            'breed': pet_instance.breed,
            'profile_pic':pet_instance.profile_pic
        })

    context = {
        'form': form, 
        'pet_instance': pet_instance
    }
    return render(request, 'edit_pet.html', context)
        

def profilePage(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        o_form = OwnerUpdateForm(request.POST, request.FILES, instance=request.user.owner)
        if u_form.is_valid() and o_form.is_valid():
            u_form.save()
            o_form.save()
            messages.success(request, f'profile has been updated')
            return redirect('profile')
    else: 
        u_form = UserUpdateForm(instance=request.user)
        o_form = OwnerUpdateForm(instance=request.user.owner)
    

    context = {
        'u_form' : u_form,
        'o_form' : o_form,
    }
    
    return render(request, 'profile.html', context)


def registerPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        form = CreateUserForm()

        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            if form.is_valid():
                user = form.save()
                username = form.cleaned_data.get('username')
                messages.success(request,'Account was successfully created!')

                return redirect('login')

        context = {'form':form}
        return render(request, 'register.html', context)


def loginPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:

        if request.method =='POST':
            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.info(request,'username OR password is incorrect')

        context = {}
        return render(request, 'login.html', context)


def logoutUser(request):
    logout(request)    
    return redirect('home')


def home(request):
    context={}
    return render(request, "home.html", context)


@login_required
def customer_booking(request):
    owner = request.user.owner
    bookings = Booking.objects.filter(owner=owner, )
    
    
    context = {
        'bookings': bookings,
    }
    
    return render(request, 'customer_booking.html', context)


def feedback(request):
    feedback = Feedback.objects.all()
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        if rating:
            try:
                rating = int(rating)
                feedback_entry = Feedback(owner=request.user.owner,rating=rating, comment=comment)
                feedback_entry.save()
                return JsonResponse({'status': 'success', 'message': 'Feedback received', 'rating': rating, 'comment': comment, 'owner': request.user.owner.user.username})
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Invalid rating value'})
    feedback = Feedback.objects.all()
    return render(request, 'feedback.html',{'feedback': feedback})