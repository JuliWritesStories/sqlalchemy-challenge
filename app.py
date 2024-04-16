# Import the dependencies.
import sqlalchemy
import numpy as np
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################

# Create engine to connect to the SQLite database.
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect an existing database into a new model.
Base = automap_base()

# Reflect the tables.
Base.prepare(autoload_with=engine)

# Save references to each table.
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB.
app = Flask("Hawaii")

#################################################
# Flask Setup
#################################################

# Define the home route.
@app.route('/')
def home():
    return (
        f"Climate Analysis API<br/><br/>"
        f"Routes: <br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start<br/>"
        f"/api/v1.0/startend<br/>"
    )

# Define the precipitation route.
@app.route('/api/v1.0/precipitation')
def precipitation():
    # Connect to the database session.
    session = Session(engine)
    
    # Find the most recent date in the database.
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    
    # Calculate the date one year ago from the most recent date.
    one_year_ago = datetime.strptime(most_recent_date, '%Y-%m-%d') - timedelta(days=365)
    
    # Query for precipitation data for the last year.
    precipitation_data = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= one_year_ago).all()
    
    # Close the session.
    session.close()
    
    # Convert precipitation data to dictionary format.
    precipitation_dict = {date: prcp for date, prcp in precipitation_data}
    
    # Return the JSON representation of the dictionary.
    return jsonify(precipitation_dict)

# Define the stations route.
@app.route("/api/v1.0/stations")
def station():
    # Connect to the database session.
    session = Session(engine)
    
    # Query for the list of stations.
    results = session.query(Measurement.station.distinct()).all()
    
    # Extract station names from the query results.
    stations = [station[0] for station in results]
    
    # Close the session.
    session.close()  
    
    # Return the JSON representation of the list of stations.
    return jsonify(stations)    

# Define the temperature observations route.
@app.route('/api/v1.0/tobs')
def tobs():
    # Connect to the database session.
    session = Session(engine)
    
    # Query for the most active station.
    most_active_station = session.query(Measurement.station).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).\
        first() 
    
    # Check if a most active station is found.
    if most_active_station:
        # Query for temperature observations for the last year at the most active station.
        latest_date = session.query(func.max(Measurement.date)).scalar()
        latest_date = datetime.strptime(latest_date, '%Y-%m-%d')
        one_year_ago = latest_date - timedelta(days=365)
        results = session.query(Measurement.date, Measurement.tobs).\
            filter(Measurement.station == most_active_station[0],
                   Measurement.date >= one_year_ago).\
            order_by(Measurement.date).all() 
        
        # Close the session.
        session.close()
        
        # Convert temperature observations to list of dictionaries.
        tobs_list = [{'Date': date, 'Temperature': tobs} for date, tobs in results]
        
        # Return the JSON representation of the list of temperature observations.
        return jsonify(tobs_list)
    else:
        # Close the session.
        session.close()
        
        # Return a JSON response indicating failure.
        return jsonify({'failure'})

# Define the route for temperature data starting from a given date.
@app.route("/api/v1.0/<start>")
def start_date(start):
    # Connect to the database session.
    session = Session(engine)
    
    # Query for temperature data starting from the given date.
    starting_temperature_dates = session.query(Measurement.date,
                                                func.min(Measurement.tobs),
                                                func.avg(Measurement.tobs),
                                                func.max(Measurement.tobs)).\
                                        filter(Measurement.date >= start).\
                                        group_by(Measurement.date).all() 
    
    # Close the session.
    session.close() 
    
    # Convert temperature data to list of dictionaries.
    starting_temperatures = [{"Date": temp[0], "TMIN": temp[1], "TAVG": temp[2], "TMAX": temp[3]} for temp in starting_temperature_dates]
    
    # Return the JSON representation of the list of temperature data.
    return jsonify(starting_temperatures)

# Define the route for temperature data between two given dates.
@app.route("/api/v1.0/<start>/<end>")
def start_end_dates(start, end):
    # Connect to the database session.
    session = Session(engine)
    
    # Query for temperature data between the given dates.
    end_date_temperatures = session.query(Measurement.date,
                                            func.min(Measurement.tobs),
                                            func.avg(Measurement.tobs),
                                            func.max(Measurement.tobs)).\
                                    filter(Measurement.date >= start).\
                                    filter(Measurement.date <= end).\
                                    group_by(Measurement.date).all()
    
    # Close the session.
    session.close() 
    
    # Convert temperature data to list of dictionaries.
    start_end_temps = [{"Date": temp[0], "TMIN": temp[1], "TAVG": temp[2], "TMAX": temp[3]} for temp in end_date_temperatures]
    
    # Return the JSON representation of the list of temperature data.
    return jsonify(start_end_temps)

# Define a test route.
@app.route("/api/v1.0/<test>")
def test(test):
    return test

# Run the Flask app.
if __name__ == '__main__':
    app.run(debug=True)
