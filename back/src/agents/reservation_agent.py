"""
Reservation Agent - Handles table reservations
"""
from typing import Dict, Any, Optional, List
from smolagents import ToolCallingAgent
from datetime import datetime
import re

class ReservationAgent(ToolCallingAgent):
    """
    Reservation Agent that handles table reservations for the restaurant.
    Manages booking details, availability checking, and reservation confirmation.
    """
    
    def __init__(self):
        """Initialize the reservation agent"""
        self.reservations: List[Dict[str, Any]] = []
        self.orchestrator = None
        self.restaurant_capacity = {
            'total_tables': 20,
            'table_sizes': {
                2: 8,   # 8 tables for 2 people
                4: 6,   # 6 tables for 4 people  
                6: 4,   # 4 tables for 6 people
                8: 2    # 2 tables for 8 people
            }
        }
        
    def execute(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute user input related to reservations
        
        Args:
            user_input: User's input text
            context: Additional context about the request
            
        Returns:
            Dictionary containing the result of the execution
        """
        if context is None:
            context = {}
            
        # Store orchestrator reference if provided
        if 'orchestrator' in context:
            self.orchestrator = context['orchestrator']
            
        try:
            # Extract reservation details from user input
            reservation_details = self._extract_reservation_details(user_input)
            
            if not reservation_details:
                # Ask for clarification if details are missing
                return self._ask_for_missing_details(user_input)
            
            # Check availability
            availability = self._check_availability(reservation_details)
            
            if not availability['available']:
                return {
                    'success': False,
                    'message': f"Désolé, nous n'avons pas de table disponible pour {reservation_details['guests']} personnes le {reservation_details['date']} à {reservation_details['time']}. {availability['suggestion']}",
                    'type': 'reservation',
                    'data': {'available': False, 'suggestion': availability['suggestion']}
                }
            
            # Create the reservation
            created_reservation = self._create_reservation(reservation_details)
            
            return {
                'success': True,
                'message': f"Réservation confirmée pour {created_reservation['name']} le {created_reservation['date']} à {created_reservation['time']} pour {created_reservation['guests']} personnes. Merci!",
                'type': 'reservation',
                'data': created_reservation
            }
            
        except Exception as e:
            print(f"[RESERVATION_AGENT] Error processing reservation: {e}")
            return {
                'success': False,
                'message': f"Désolé, une erreur est survenue lors de la réservation: {str(e)}",
                'error': str(e)
            }
    
    def _extract_reservation_details(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Extract reservation details from user input
        """
        details = {}
        user_input_lower = user_input.lower()
        
        # Extract name
        name_match = re.search(r'(je m\'appelle|mon nom est|nom:?|pour)\s*([\w\s-]+)', user_input_lower)
        if name_match:
            details['name'] = name_match.group(2).strip().title()
        
        # Extract date
        date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre))', user_input_lower)
        if date_match:
            details['date'] = date_match.group(1).strip()
        else:
            # Try to find day names
            day_match = re.search(r'(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)', user_input_lower)
            if day_match:
                details['date'] = day_match.group(1).strip()
        
        # Extract time
        time_match = re.search(r'(\d{1,2}[h:.]\d{2}|\d{1,2}\s*[h:.]\s*\d{2}|\d{1,2}\s*(heure|h))', user_input_lower)
        if time_match:
            details['time'] = time_match.group(1).strip()
        else:
            # Try common time expressions
            if 'midi' in user_input_lower:
                details['time'] = '12:00'
            elif 'soir' in user_input_lower:
                details['time'] = '19:00'
        
        # Extract number of guests
        guests_match = re.search(r'(\d+)\s*(personne|personnes|convive|convivess|couvert|couverts)', user_input_lower)
        if guests_match:
            details['guests'] = int(guests_match.group(1))
        
        # Extract phone number
        phone_match = re.search(r'(\+?\d{2}\s?\d{1}\s?\d{2}\s?\d{2}\s?\d{2}|\d{10})', user_input)
        if phone_match:
            details['phone'] = phone_match.group(1).strip()
        
        # If we have at least name, date, time, and guests, consider it valid
        if all(key in details for key in ['name', 'date', 'time', 'guests']):
            # Set default phone if not provided
            details['phone'] = details.get('phone', 'Non spécifié')
            return details
        
        return None
    
    def _ask_for_missing_details(self, user_input: str) -> Dict[str, Any]:
        """
        Ask for missing reservation details
        """
        missing = []
        
        # Check what's missing based on common patterns
        if 'réservation' in user_input.lower() or 'réserver' in user_input.lower():
            if not any(word in user_input.lower() for word in ['m\'appelle', 'nom', 'pour']):
                missing.append('votre nom')
            if not any(word in user_input.lower() for word in ['personne', 'personnes', 'couvert', 'convivess']):
                missing.append('le nombre de personnes')
            if not any(word in user_input.lower() for word in ['le ', 'aujourd\'hui', 'demain', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']):
                missing.append('la date')
            if not any(word in user_input.lower() for word in ['heure', 'midi', 'soir', 'h', ':']):
                missing.append('l\'heure')
        
        if missing:
            missing_list = ', '.join(missing)
            return {
                'success': False,
                'message': f"Pour faire une réservation, j'ai besoin de {missing_list}. Pouvez-vous préciser?",
                'type': 'reservation',
                'data': {'missing_details': missing}
            }
        
        # Default clarification
        return {
            'success': False,
            'message': "Pour faire une réservation, j'ai besoin de votre nom, la date, l'heure et le nombre de personnes. Pouvez-vous fournir ces informations?",
            'type': 'reservation',
            'data': {'missing_details': ['nom', 'date', 'heure', 'nombre de personnes']}
        }
    
    def _check_availability(self, reservation_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check availability for a reservation
        """
        # Simple availability check - in a real system, this would check against existing reservations
        # For now, we'll simulate some basic availability logic
        
        # Convert date to comparable format (simplified)
        date_str = reservation_details['date']
        time_str = reservation_details['time']
        guests = reservation_details['guests']
        
        # Check if we have tables that can accommodate the party size
        available_table_size = None
        for size, count in self.restaurant_capacity['table_sizes'].items():
            if size >= guests and count > 0:
                available_table_size = size
                break
        
        if not available_table_size:
            return {
                'available': False,
                'suggestion': f"Nous n'avons pas de table assez grande pour {guests} personnes. Notre plus grande table est pour 8 personnes."
            }
        
        # Simulate some busy times (evenings are busier)
        try:
            # Parse time to check if it's evening
            time_parts = re.findall(r'\d+', time_str)
            if time_parts:
                hour = int(time_parts[0])
                if hour >= 18:  # Evening
                    # 30% chance of being full in the evening (simulation)
                    import random
                    if random.random() < 0.3:
                        return {
                            'available': False,
                            'suggestion': "Nous sommes complets à cette heure. Avez-vous une autre heure ou date qui vous conviendrait?"
                        }
        except:
            pass
        
        return {
            'available': True,
            'suggestion': "Nous avons des tables disponibles."
        }
    
    def _create_reservation(self, reservation_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new reservation
        """
        # Generate reservation ID
        reservation_id = f"RES-{len(self.reservations) + 1:04d}"
        
        # Create reservation record
        reservation = {
            'reservation_id': reservation_id,
            'name': reservation_details['name'],
            'phone': reservation_details['phone'],
            'date': reservation_details['date'],
            'time': reservation_details['time'],
            'guests': reservation_details['guests'],
            'status': 'confirmed',
            'created_at': datetime.now().isoformat(),
            'special_requests': ''
        }
        
        # Add to reservations list
        self.reservations.append(reservation)
        
        print(f"[RESERVATION_AGENT] Created reservation {reservation_id} for {reservation['name']}")
        
        return reservation
    
    def get_reservation(self, reservation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a reservation by ID
        """
        for reservation in self.reservations:
            if reservation['reservation_id'] == reservation_id:
                return reservation
        return None
        
    def get_reservations_by_name(self, name: str) -> List[Dict[str, Any]]:
        """
        Get reservations by customer name
        """
        return [r for r in self.reservations if r['name'].lower() == name.lower()]
        
    def cancel_reservation(self, reservation_id: str) -> bool:
        """
        Cancel a reservation
        """
        for i, reservation in enumerate(self.reservations):
            if reservation['reservation_id'] == reservation_id:
                self.reservations[i]['status'] = 'cancelled'
                print(f"[RESERVATION_AGENT] Cancelled reservation {reservation_id}")
                return True
        return False
        
    def get_available_slots(self, date: str, party_size: int) -> List[Dict[str, Any]]:
        """
        Get available time slots for a given date and party size
        """
        # Simulated available slots - in a real system, this would check actual availability
        slots = [
            {'time': '12:00', 'available': True},
            {'time': '12:30', 'available': True},
            {'time': '13:00', 'available': True},
            {'time': '19:00', 'available': True},
            {'time': '19:30', 'available': True},
            {'time': '20:00', 'available': True},
            {'time': '20:30', 'available': True},
            {'time': '21:00', 'available': True}
        ]
        
        return slots
        
    def get_reservation_count(self) -> int:
        """
        Get the total number of reservations
        """
        return len(self.reservations)