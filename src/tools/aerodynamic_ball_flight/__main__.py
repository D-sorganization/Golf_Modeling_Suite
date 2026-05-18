import sys
import logging
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
import pyvista as pv
from pyvistaqt import QtInteractor

from src.shared.python.physics.ball_enhanced_simulator import EnhancedBallFlightSimulator
from src.shared.python.physics.ball_launch_conditions import LaunchConditions

logger = logging.getLogger(__name__)

class AeroBallFlightWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aerodynamic Ball Flight Simulator")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.plotter = QtInteractor(self)
        layout.addWidget(self.plotter.interactor)

        self.btn_simulate = QPushButton("Simulate Aerodynamic Flight")
        self.btn_simulate.clicked.connect(self.run_simulation)
        layout.addWidget(self.btn_simulate)

        self.simulator = EnhancedBallFlightSimulator()

    def run_simulation(self):
        logger.info("Running aerodynamic ball flight simulation...")
        self.plotter.clear()

        # Simple launch conditions
        launch = LaunchConditions(
            velocity=70.0,
            launch_angle=0.2, # ~11.5 deg
            azimuth_angle=0.0,
            spin_rate=2500.0,
            spin_axis=np.array([0.0, -1.0, 0.0])
        )

        trajectory = self.simulator.simulate_trajectory(launch)
        
        points = []
        for p in trajectory:
            points.append(p.position)

        if points:
            poly = pv.MultipleLines(points=points)
            self.plotter.add_mesh(poly, color="blue", line_width=2)
            
            # Start and End markers
            start_sphere = pv.Sphere(radius=0.5, center=points[0])
            end_sphere = pv.Sphere(radius=0.5, center=points[-1])
            self.plotter.add_mesh(start_sphere, color="white")
            self.plotter.add_mesh(end_sphere, color="red")

        self.plotter.add_axes()
        self.plotter.reset_camera()

def main():
    logging.basicConfig(level=logging.INFO)
    app = QApplication(sys.argv)
    window = AeroBallFlightWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
