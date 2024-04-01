from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

def check_clinic_availability(postal_code, reason):
    clinics = [
        ["Clinic A", ["cold", "flu"], "B4P2R2", (44.6820, -63.7443)],  # Example coordinates for Clinic A
        ["Clinic B", ["broken bone", "sprain"], "C2T1A3", (44.6488, -63.5752)],  # Example coordinates for Clinic B
        ["Clinic C", ["headache", "migraine"], "D1E4F5", (44.6475, -63.5906)],  # Example coordinates for Clinic C
        ["Clinic D", ["cold", "flu"], "E5G3H2", (44.6654, -63.5652)],  # Example coordinates for Clinic D
        ["Clinic E", ["broken bone", "sprain"], "F6I7J8", (44.6665, -63.6005)],  # Example coordinates for Clinic E
        ["Clinic F", ["headache", "migraine"], "G9K1L2", (44.6623, -63.5918)],  # Example coordinates for Clinic F
        ["Clinic G", ["cold", "flu"], "H3M4N5", (44.6825, -63.5745)],  # Example coordinates for Clinic G
        ["Clinic H", ["broken bone", "sprain"], "I6O7P8", (44.6611, -63.5782)]  # Example coordinates for Clinic H
    ]

    matching_clinics = []
    for clinic in clinics:
        clinic_name = clinic[0]
        clinic_reasons = clinic[1]
        clinic_postal_code = clinic[2]
        clinic_coordinates = clinic[3]

        if reason in clinic_reasons and postal_code[:3] == clinic_postal_code[:3]:
            matching_clinics.append(clinic_name)

    # If no matching clinics found, find the closest clinic
    if not matching_clinics:
        user_coordinates = (44.6488, -63.5752)  # Example coordinates for user location (Halifax)
        closest_clinic = min(clinics, key=lambda x: distance(user_coordinates, x[3]))[0]
        return [closest_clinic]

    return matching_clinics

def distance(coord1, coord2):
    # Simple Euclidean distance calculation for demonstration purposes
    return ((coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2) ** 0.5


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    postal_code = request.form['postal_code']
    reason = request.form['reason']
    matching_clinics = check_clinic_availability(postal_code.upper(), reason.lower())
    return jsonify({'clinics': matching_clinics})

if __name__ == '__main__':
    app.run(debug=True)
