# gui2.py
# Kenneth Lipke
# Spring 2018

"""
Gui Version 2.0 -- refactoring and cleaning up of the code
"""

import tkinter as tk
from tkinter.filedialog import askopenfilename, askdirectory, asksaveasfilename
from tkinter import messagebox

import pandas as pd

# My helper classes 
from Requirement import *
from Popup import *
from MenuBar import *
from Optimizer import *

# Helper functions
import clean_data


class MainApplication(tk.Frame):
	"""
	Main application for the user interface, allows the user to select the
	required files to make the schedule, as well as creating the intermediate
	sheets for them to use

	Key Attributes
	--------------


	Key Methods
	-----------


	"""

	def __init__(self, parent, *args, **kwargs):
		"""
		Creates the main window for the GUI
		Includes a frame for:
			File Selection
			Requirements
			Optimization
			Results

		Parameters
		----------
		parent - the tkinter root

		"""

		# master window
		self.master = parent


		self.initial_file_df = None
		self.courses = None
		self.course_list_selected = False
		self.LP_input = None
		self.teacher_df = None
		self.ms_preference_df = None
		self.hs_preference_df = None
		self.preference_input_df = None
		self.prox = None

		self.requirements = []

		self.optimization_output_directory = None

		# Setup menubar
		self.menubar = MenuBar(self)
		print(self.menubar)
		self.master.config(menu=self.menubar.menu)

		# Override window close button
		# self.master.protocol('WM_DELETE_WINDOW', self.menubar.file_quit)
		# Uncomment when done debugging


		#----------------------------------------------------------
		#					File Selection Frame
		#----------------------------------------------------------
		"""
		Grid layout (5x3)
		label prompt & select button & label displaying the file name
		"""
		# Create the frame
		self.file_select_frame = tk.Frame(parent, bd=5, relief=tk.RAISED)
		self.file_select_frame.pack(pady=10)

		# Frame Title
		tk.Label(self.file_select_frame, text="File Selection and Creation",
			font=("Helvetica", 18)).grid(row=0, column=1, columnspan=3)

		# First file
		s = "Step 1: Please select the file list all courses:"
		tk.Label(self.file_select_frame, text=s).grid(row=1, column = 1,
			stick="W")
		tk.Button(self.file_select_frame, text="Select",
			command=self.get_initial_file).grid(row=1, column=2)

		# Button to create second file for them to fill out
		s = "Step 2: Create file to fill in teachers"
		s += "\n(select where it should be saved): "
		tk.Label(self.file_select_frame, text=s).grid(row=2, column=1,
			sticky="W")
		tk.Button(self.file_select_frame, text="Make File", 
			command = self.make_teacher_file).grid(row=2, column=2)

		# Completed Teacher file
		s = "Step 3: Select file with teacher mapping: "
		tk.Label(self.file_select_frame, text=s).grid(row=3, column=1,
			sticky="W")
		tk.Button(self.file_select_frame, text="Select", 
			command=self.get_teacher_file).grid(row=3, column=2)

		# Make spreadsheet for student preferenfes, and LP input
		s = "Step 4: Generate preference form: "
		s += "\n(select where it should be saved)"
		tk.Label(self.file_select_frame, text=s).grid(row=4, column=1, 
			sticky="W")
		tk.Button(self.file_select_frame, text="Make File",
			command=self.make_preference_form).grid(row=4, column=2)

		# Upload student preferences
		s = "Step 5: Upload MS Student preferences:"
		tk.Label(self.file_select_frame, text=s).grid(row=5, column=1,
			sticky="W")
		tk.Button(self.file_select_frame, text="Select", 
			command=self.get_ms_preference_file).grid(row=5, column=2)

		s = "Step 6: Upload HS Student preferences:"
		tk.Label(self.file_select_frame, text=s).grid(row=6, column=1,
			sticky="W")
		tk.Button(self.file_select_frame, text="Select", 
			command=self.get_hs_preference_file).grid(row=6, column=2)


		#----------------------------------------------------------
		#					Add RequirementFrame
		#----------------------------------------------------------
		# Create and pack the frame
		self.req_frame = tk.Frame(parent, bd=5, relief=tk.RAISED)
		self.req_frame.pack(pady=10)

		# Add a Frame Label
		tk.Label(self.req_frame, text="Required Courses", 
			font=("Helvetica", 18)).pack()

		# Upper frame (contains buttons)
		self.req_frame_upper = tk.Frame(self.req_frame)
		self.req_frame_upper.pack()

		# Button to add req
		self.add = tk.Button(self.req_frame_upper, text="Add Requirement",
			command = self.add_req)
		self.add.grid(row=1, column=1)

		# Add button to delete requirement
		self.delete = tk.Button(self.req_frame_upper, text="Remove Requirement",
			command = self.del_req)
		self.delete.grid(row=1, column=2)

		# Add label saying what to do
		s = "Add Requirements: Once Step 1 is completed, and a document containing"
		s += "\n a column `Course Name` is found, you can add grade level requirements"
		tk.Label(self.req_frame_upper, text=s).grid(row=0, column=1, columnspan=2)

		# Lower frame, contains the requirements (uppded when added)
		self.req_frame_lower = tk.Frame(self.req_frame, bd=2, relief=tk.RIDGE)
		self.req_frame_lower.pack(padx=5, pady=5)


		#----------------------------------------------------------
		#					Optimization Frame
		#----------------------------------------------------------
		"""
		Button to save the current configuration
		Button to load a previously saved configuration
		Slider to set optimizaiton speed (inverse MIPGap)
		Button to start optimization

		set up with a grid layout
		"""
		self.opt_frame = tk.Frame(self.master, bd=5, relief=tk.RAISED)
		self.opt_frame.pack(pady=10)

		# Create title for frame
		tk.Label(self.opt_frame, text="Optimization Menu",
			 font=("Helvetica", 18)).grid(row=1, column=1, columnspan=2)

		# Add save/open button (tied to menubar function)
		tk.Button(self.opt_frame, text="Save Configuration",
			command = self.menubar.save).grid(row=2, column=1, padx=15)
		tk.Button(self.opt_frame, text="Open Configuration",
			command = self.menubar.open).grid(row=2, column=2, padx=15)

		# Add MIPGap slider
		tk.Label(self.opt_frame, text="Speed Adjust (smaller is slower)").grid(
			row=3, column=1, columnspan=2)
		self.slider = tk.Scale(self.opt_frame, from_=0, to_=1,
			orient=tk.HORIZONTAL, resolution=0.01, length=200)
		self.slider.grid(row=4, column=1, columnspan=2)

		# Select Save Location
		tk.Button(self.opt_frame, text="Select Save Location", 
			command=self.set_opt_output_loc).grid(row=5, column=1, 
			columnspan=2, pady=5)

		# Optimize Button
		tk.Button(self.opt_frame, text="Create Schedule",
			 highlightbackground="red", pady=2, width=20, height=4,
			 font=("Helvetica", 14, "bold"),
			 command = self.optimize).grid(row=6,
			column=1, columnspan=2, pady=15)




	#----------------------------------------------------------
	#					File Selection Methods
	#----------------------------------------------------------

	def get_initial_file(self):
		"""
		Saves down the intial file from the first button,
		this file should have all the course names, as well as other relevant
		course information (minus teachers)
		"""
		# save the file name
		initial_file_name = askopenfilename()
		#df = pd.read_csv(initial_file_name)
		df = pd.read_excel(initial_file_name) # <-- it is an excel file
		self.initial_file_df = df

		# make sure it has the right column header
		if "Course Name" not in df.columns:
			messagebox.showerror("Error", 
				"File must have a column for `Course Name`")
			return 

		# get the course list
		self.courses = df["Course Name"]
		self.course_list_selected = True

		# Create a label for the UI
		tk.Label(self.file_select_frame,
			text = "  " + self.get_file_name(initial_file_name)
			).grid(row=1, column=3)

	def get_file_name(self, file):
		"""
		Returns the name of the file after the last /
		"""
		return file[file.rfind("/") + 1:]

	def make_teacher_file(self):
		"""
		Takes the initial file (with all courses and info, etc.) and uses
		the clean_data functions to create the second form to fill out
		the one that ties courses to teachers

		Requires
		--------
		self.initial_file_df is NOT None, this can either have been selected, or 
		saved in a previous configuration
		"""

		print("Running Junstina's function")

		# make sure we have an initial file to work with
		if self.initial_file_df is None:
			# Alert the user with message box
			messagebox.showerror("Error",
			"Must have completed step one, or loaded a previous configuration")
			return

		# Continue with file creation
		dir_name = askdirectory()
		intermediate_df = clean_data.create_teacher_info(self.initial_file_df, dir_name)
		#				  ^^ function from Justina's clean_data

		# Create the final dataframe for LP input
		self.LP_input = clean_data.create_LP_input(intermediate_df, self.initial_file_df)
		#               ^^ function from Justina

		# Create the proximity matrix
		self.prox = clean_data.dept_proximity(self.LP_input)
		
		# self.LP_input.to_csv("LP_Input.csv")
		# print(self.LP_input)
		# print(dir_name)
		

	def get_teacher_file(self):
		"""
		gets the teacher file
		"""
		# get the file
		teacher_file_name = askopenfilename()

		# make the label
		tk.Label(self.file_select_frame,
			text = "  " + self.get_file_name(teacher_file_name)).grid(
			row = 3, column=3, sticky="W")
		self.teacher_df = pd.read_csv(teacher_file_name) # there is a header
		print(self.teacher_df)


	def make_preference_form(self):
		print("Add Dae Won's script to generate form")


	def get_preference_file(self):
		"""
		Selects the file for the filled out student preferences,
		then run's the scipt to turn them into useable LP inputs
		"""
		# In the interum, as don't know where that script is
		# just use the flattened for testing
		s = "Waiting on Justina's Prefernce Script, for now, just select"
		s+= " the flattened preference so we having some file to test with"
		messagebox.showinfo("Alert", s)



		completed_preference_file_name = askopenfilename()
		tk.Label(self.file_select_frame, 
			text = " " + self.get_file_name(completed_preference_file_name)
			).grid(row=5, column=3, sticky="W")

		print("Run Justina's script to make LP input preferences")

		self.preference_input_df = pd.read_csv(completed_preference_file_name)

	def get_ms_preference_file(self):
		"""
		Gets the middle school preference file, and checks if highschool
		file is also uploaded, if so, then it creates full file
		"""
		file = askopenfilename()
		tk.Label(self.file_select_frame, 
			text = " " + self.get_file_name(file)
			).grid(row=5, column=3, sticky="W")
		# self.ms_preference_df = pd.read_csv(file)
		self.ms_preference_df = pd.DataFrame.from_csv(file)

		if self.hs_preference_df is not None:
			self.combine_prefs()


	def get_hs_preference_file(self):
		"""
		Gets the high school preference file,
		check is the middle school file is also uploaded, 
		if so creates combined df
		"""
		file = askopenfilename()
		tk.Label(self.file_select_frame, 
			text = " " + self.get_file_name(file)
			).grid(row=6, column=3, sticky="W")
		self.hs_preference_df = pd.DataFrame.from_csv(file)

		if self.ms_preference_df is not None:
			self.combine_prefs()


	def combine_prefs(self):
		"""
		Combines the hs and middle school files to create the 
		preference inpute df for the optimizer
		"""
		# import course data from LP_Input.csv
		# the index should be the list of courses + the V2 courses.
		# course_list = pd.DataFrame.from_csv("LP_Input.csv")
		# course_list = list(course_list.index)
		course_list = list(self.LP_input["Course Name"])

		# hs_response = pd.DataFrame.from_csv("School form - High School form responses.csv")
		# ms_response = pd.DataFrame.from_csv("School form - Middle School form responses.csv")
		ms_response = self.ms_preference_df
		hs_response = self.hs_preference_df

		hs_data = hs_response.iloc[:, 2:-2]
		ms_data = ms_response.iloc[:, 2:-2]

		# extract preference levels from the column names

		temp_list = hs_response.columns[2:-2]
		temp_list2 = ms_response.columns[2:-2]

		# extracted choice numbers from the column names 
		hs_choices = []
		ms_choices = []

		for item in temp_list:
		    hs_choices.append(int(item[-2]))
		    
		for item in temp_list2:
		    ms_choices.append(int(item[-2]))
		    
		# initialize final result of the preprocessing
		result = pd.DataFrame(0,columns = course_list, index = range(hs_data.shape[0]+ms_data.shape[0]))

		# helper function which returns the corresponding indices in course_list for each row of responses
		def course_index(input_array):
		    indices = []
		    for item in input_array:
		        indices.append(course_list.index(item))
		    return np.array(indices)

		for i in range(hs_data.shape[0]):
		    # assign hs_choices values to the corresponding indices in the result data
		    result.iloc[i,course_index(hs_data.iloc[i,:])] = hs_choices

		    
		ms_start_index = hs_data.shape[0]
		for i in range(ms_data.shape[0]):
		    # assign middle school choices. Row index is num_rows of hs_data + i
		    # (so MS rows would be after HS rows in result)
		    result.iloc[(ms_start_index + i),course_index(ms_data.iloc[i,:])] = ms_choices
		    
		self.preference_input_df = result
		print(self.preference_input_df)



	#----------------------------------------------------------
	#					Requirement Methods
	#----------------------------------------------------------
	def add_req(self):
		"""
		Adds requirements, creates a popup window with the prompts to add
		requirements, pulls course list from a selected file
		-----> COME BACK AND SPECIFY WHICH FILE <---------
		"""
		# Verify course list is found
		if self.course_list_selected == False:
			messagebox.showinfo("Alert", "Must select course file first")
			return 

		# Create new window
		pop = tk.Toplevel()
		f = tk.Frame(pop)
		f.pack()

		# Label
		l1 = tk.Label(f, text="Students in Grade", justify='left')
		l1.pack(side='left')

		# Grade Select
		grade_options = [5,6,7,8,9,10,11,12]
		grade = tk.IntVar(pop)
		grade.set(5)
		grade_menu = tk.OptionMenu(f, grade, *tuple(grade_options))
		grade_menu.pack(side='left')

		# Middle Label
		l2 = tk.Label(f, text="Must take", justify='left')
		l2.pack(side='left')

		# Course select
		Courses = ["Math", "Science", "English"]
		course1 = tk.StringVar(f)
		course1.set("None")
		choose1 = tk.OptionMenu(f, course1, *tuple(list(self.courses)))
		choose1.pack(side='left')

		# OR label
		l3 = tk.Label(f, text="OR (leave blank if no or condition)", justify='left')
		l3.pack(side='left')

		# Course select 2
		course2 = tk.StringVar(f)
		course2.set("None")
		choose2 = tk.OptionMenu(f, course2, *tuple(list(self.courses)))
		choose2.pack(side='left')

		# Button to add
		def finished():
			"""
			(innter function)
			creates a new requirement instance, adds a label to main window
			then kills the popup window
			"""
			if course2.get() == "None":
				r = Requirement(grade.get(), course1.get())
			else:
				r = Requirement(grade.get(), course1.get(), course2.get())
			
			# add the new requirement
			self.requirements.append(r) 

			# display the new requirement 
			r.create_label(self.req_frame_lower)

			# kill this window
			pop.destroy()


		add_but = tk.Button(f, text="Add", command = finished)
		add_but.pack(side='bottom', padx=10, pady=10)


	def del_req(self):
		"""
		Creates a popup window that lists all the current requirements
		and lets you select one to delete
		"""
		pop = tk.Toplevel()
		f = tk.Frame(pop)
		f.pack()

		# Add checkboxes for all 
		del_dict = {}
		for r in self.requirements:
			del_dict[r] = tk.IntVar()
			del_dict[r].set(0)
			tk.Checkbutton(f, text=r.describe(), variable=del_dict[r]).pack()

		def done():
			"""
			(inner function)
			Deletes the requirements with checks, then closes the window
			"""
			for r in del_dict:
				if del_dict[r].get() == 1:
					# delete the labels:
					r.remove_label()
					self.requirements.remove(r)

			# closes the window when finished
			pop.destroy()

		# Finished button
		tk.Button(pop, text="Finished", 
			command = done).pack(side='bottom', pady=10)



	#-------------------------------------------------------
	#					Optimization Functions
	#-------------------------------------------------------
	def set_opt_output_loc(self):
		"""
		Sets the direcotry where the optimization output will be saved
		"""
		#dir = askdirectory()
		s = "Select the location where you would like the output to be saved.\n\n"
		s += "A folder with the name specified will be created in this location"
		s += "\n\n**DO NOT put a file extension in your input**"
		messagebox.showinfo("Note", s)
		directory = asksaveasfilename()
		self.optimization_output_directory = directory


	def optimize(self):
		"""
		Runs the schedule optimizer
		First: verifies that we have all the necessary data
		Seoncd: Checks the save location
		print("Put your function here")
		"""

		still_needed = []
		# Verify the required information
		if self.preference_input_df is None:
			still_needed.append("Preferences")
		# else:
		# 	# save it down for optimizer debugging
		# 	self.preference_input_df.to_csv("OptTestFiles/prefs2.csv")
		if self.LP_input is None:
			still_needed.append("LP_input")
		# else:
		# 	self.LP_input.to_csv("OptTestFiles/LP_input2.csv")
		if self.teacher_df is None:
			still_needed.append("Teacher File (secondary)")
		# else:
		# 	self.teacher_df.to_csv("OptTestFiles/teacher2.csv")
		# if self.optimization_output_directory is None:
		# 	still_needed.append("Save location for optimization")

		s = ""
		if len(still_needed) > 0:
			s = str(still_needed)
			messagebox.showerror("Error", "You are missing the following\n\n" + s)
			return 

		# Get GAP value from slider
		GAP = self.slider.get()

		# Create optimization instance
		# THIS CALL NEEDS TO BE FIXED; MAKE SURE EVERYTHING IN RIGHT SPOT

		# Temp of grade file, this should eventually come from the form
		grades = pd.DataFrame({'0':[1,2], '1':[8,9]})

		# # for debugging, output all the files you are sending
		# self.preference_input_df.to_csv("test_pref_input_df.csv")
		# self.LP_input.to_csv("test_LP_input.csv")
		# self.teacher_df.to_csv("test_teacher_Df.csv")
		# self.prox.to_csv("test_prox.csv")

		self.LP_input.to_csv("intermediate_LP_input.csv")
		self.LP_input = pd.read_csv("intermediate_LP_input.csv")
		self.teacher_df.to_csv("intermediate_teacher_df.csv")
		self.teacher_df = pd.read_csv("intermediate_teacher_df.csv")


		# test re-index
		#self.LP_input = self.LP_input.reindex(range(self.LP_input.shape[0]))

		O = Optimizer(prefs = self.preference_input_df,
					LP_input = self.LP_input, 
					grades = grades,
					teacher = self.teacher_df,
					GAP = GAP,
					requirements = self.requirements,
					prox = self.prox,
					save_location  = self.optimization_output_directory)

		print("Adding Constraints")
		O.add_basic_constraints()
		O.add_max_constraint()
		#self.add_min_constraint()
		O.add_proximity_constraints()
		O.add_teacher_constraints()
		O.add_course_constraints()
		#self.add_grade_level_requirements()
		print("\n\n\n")
		print(O.Cd)
		print("\n\n")
		O.add_room_constraints()
		O.add_period_constraints()
		print("Constraints Added")

		O.set_objective()

		O.optimize()
		O.assign_value_dicts()
		O.print_grid()
		O.print_all_student_schedules()
		O.diagnostic()





if __name__ == "__main__":
    root = tk.Tk()
    root.wm_title("Schedule Optimizer")
    root["bg"] = "grey96"
    root.geometry("800x800") # fiddle with this, see if you can make it adaptive
    MainApplication(root)
    root.mainloop()