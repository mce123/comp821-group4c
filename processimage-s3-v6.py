import os
from os.path import basename
import argparse
from datetime import datetime
import threading
import subprocess
__author__ = 'MCE123'

class bcolors:
    """
    This class defines the blueprint for text decorations for the command prompt.
    Example:  print(bcolors.HEADER + "Hello World!" + bcolors.ENDC)
    Note:     If you use more than one begin text decoration, the ENDC ends all of them. If you only
              want to end only one of the text decorations, you must restart the other ones after
              where you ended them.
    """
    HEADER = '\033[95m'    #Begin Purple Text
    OKBLUE = '\033[94m'    #Begin Blue Text
    OKGREEN = '\033[92m'   #Begin Green Text
    WARNING = '\033[93m'   #Begin Yellow Text
    FAIL = '\033[91m'      #Begin RedText
    ENDC = '\033[0m'       #End All Text Decorations
    BOLD = '\033[1m'       #Begin Bold Text
    UNDERLINE = '\033[4m'  #Begin Underlined Text
    LINK      = '\x1b'     #Begin or End Hyperlink
    LINK2     = '\e]8;;'

def main():
    """
    This function runs the main program code, and makes calls to subprocedures to process file commands.
    Returns: None
    """
    bucket_path = "s3://comp821-m1.spring2018/"    #Default S3 bucket information, in the format "s3://bucket-name/".
    log_file = "tests.log"                         #Default .log file to write out results to.
    max_threads = 4                                #Default number of threads if not specified.
    highest_threads = 8                            #Highest possible number of threads, in case number specified is greater than this number.
    logging = False                                #Default - do not change this value. Logging will be enabled only if there is write access to the log_file.
    
    print('\b' + bcolors.BOLD + __file__ + ' by Patrick R. McElhiney, MCE123 (http://www.mce123.com/)' + bcolors.ENDC + '\b')
    
    #Parse Input Variables
    parser = argparse.ArgumentParser(description='This is a build-terraform script by MCE123.')
    parser.add_argument('-i','--indir', help='Input directory, implies mode Upload',required=False)
    parser.add_argument('-o','--outdir', help='Output directory, implies mode Download',required=False)
    parser.add_argument('-t','--threads', help='Number of Threads to Use', required=False)
    parser.add_argument('-d','--download', help='Path to download#.test file for list of files to download.', required=False)
    parser.add_argument('-u','--upload', help='Path to upload#.test file for list of files to upload.', required=False)
    parser.add_argument('-l','--log', help='Path to .log file to write out statistics to.', required=False)
    args = parser.parse_args()

    #Update max_threads if input is relevant
    if args.threads != None:
        if int(args.threads) != max_threads and args.threads > 0 and args.threads < (highest_threads + 1):
            max_threads = int(args.threads)

    #Update log_file if input is relevant, and enable logging if there is write access to the log_file
    if args.log != None:
        if check_file(args.log) == False:
            if check_file(args.log, 'w') != False:
                log_file = args.log
                logging = True
        else:
            log_file = args.log
            logging = True
    else:
        if check_file(log_file) == False:
            if check_file(log_file, 'w') == True:
                logging = True
        else:
            logging = True

    #Initialize blank set of logging messages
    log_messages = []

    #Initialize Start Time
    start_time = datetime.now()
    log_messages.append('New Test Started at ' + str(start_time))
    
    #Verify Input of -i or -o, since neither are required
    if args.indir == None and args.outdir == None and args.download == None and args.upload == None:
        print(bcolors.FAIL + "Error: You must specify an input or output directory, or an upload or download .test file." + bcolors.ENDC)
        return None
    elif args.indir != None and args.outdir == None and args.download == None and args.upload == None:
        print(bcolors.WARNING + "Mode: " + bcolors.ENDC + "Upload")
        log_messages.append('Test Mode: Upload')
        dir_validate = check_dir(args.indir)
        dir_valid = dir_validate[0]
        dir_path = dir_validate[1]
        if dir_valid == True:
            print(bcolors.WARNING + "Input Directory: " + bcolors.ENDC + args.indir)
            log_messages.append('Input Directory: ' + args.indir)
            log_messages.append('Bucket Path: ' + bucket_path)
            log_messages.append('Max Threads: ' + str(max_threads))
            count_files = upload(dir_path, bucket_path, max_threads)
            log_messages.append('Number of Files Processed: ' + str(count_files))
    elif args.outdir != None and args.indir == None and args.download == None and args.upload == None:
        print(bcolors.WARNING + "Mode: " + bcolors.ENDC + "Download")
        log_messages.append('Test Mode: Download')
        dir_validate = check_dir(args.outdir)
        dir_valid = dir_validate[0]
        dir_path = dir_validate[1]
        if dir_valid == True:
            print(bcolors.WARNING + "Output Directory: " + bcolors.ENDC + dir_path)
            log_messages.append('Output Directory: ' + dir_path)
            log_messages.append('Bucket Path: ' + bucket_path)
            log_messages.append('Max Threads: ' + str(max_threads))
            count_files = download(dir_path, bucket_path, max_threads)
            log_messages.append('Number of Files Processed: ' + str(count_files))
        else:
            try:
                print("Creating new directory: " + args.outdir)
                os.mkdir(args.outdir)
            except:
                print(bcolors.FAIL + "Error: Invalid File Permissions While Trying to Create Directory " + args.outdir + bcolors.ENDC)
                return None
            print(bcolors.WARNING + "Output Directory: " + bcolors.ENDC + dir_path)
            log_messages.append('Output Directory: ' + dir_path)
            log_messages.append('Bucket Path: ' + bucket_path)
            log_messages.append('Max Threads: ' + str(max_threads))
            count_files = download(args.outdir, bucket_path, max_threads)
            log_messages.append('Number of Files Processed: ' + str(count_files))
    #Verify input if -u or -d, since neither are required
    elif args.download != None and args.upload == None and args.indir == None and args.outdir != None:
        print(bcolors.WARNING + "Mode: " + bcolors.ENDC + "Download With .test File")
        log_messages.append('Test Mode: Download with .test File')
        dir_validate = check_dir(args.outdir)
        dir_valid = dir_validate[0]
        dir_path = dir_validate[1]
        file_validate = check_file(args.download)
        if dir_valid == True:
            if file_validate == True:
                print(bcolors.WARNING + "Input .test File: " + bcolors.ENDC + args.download)
                log_messages.append('Input .test File: ' + args.download)
                log_messages.append('Bucket Path: ' + bucket_path)
                log_messages.append('Max Threads: ' + str(max_threads))
                count_files = download_test(args.download, args.outdir, bucket_path, max_threads)
                log_messages.append('Number of Files Processed: ' + str(count_files))
            else:
                print(bcolors.FAIL + "Input .test File: " + args.download + " is not valid.")
                return None
        else:
            if file_validate == True:
                try:
                    print("Creating new directory: " + args.outdir)
                    os.mkdir(args.outdir)
                except:
                    print(bcolors.FAIL + "Error: Invalid File Permissions While Trying to Create Directory " + args.outdir + bcolors.ENDC)
                    return None
                print(bcolors.WARNING + "Input .test File: " + bcolors.ENDC + args.download)
                log_messages.append('Input .test File: ' + args.download)
                log_messages.append('Bucket Path: ' + bucket_path)
                log_messages.append('Max Threads: ' + str(max_threads))
                count_files = download_test(args.download, args.outdir, bucket_path, max_threads)
                log_messages.append('Number of Files Processed: ' + str(count_files))
            else:
                print(bcolors.FAIL + "Input .test File: " + args.download + " is not valid.")
                return None
    elif args.download != None and args.upload == None and args.indir == None and args.outdir == None:
        print(bcolors.FAIL + "Error: You didn't specify an output directory! Add -o ./dir_path to your input arguments." + bcolors.ENDC)
        return None
    elif args.download == None and args.upload != None and args.indir == None and args.outdir == None:
        print(bcolors.WARNING + "Mode: " + bcolors.ENDC + "Upload With .test File")
        log_messages.append('Test Mode: Upload with .test File')
        file_validate = check_file(args.upload)
        if file_validate == True:
            print(bcolors.WARNING + "Input .test File: " + bcolors.ENDC + args.upload)
            log_messages.append('Input .test File: ' + args.upload)
            log_messages.append('Bucket Path: ' + bucket_path)
            log_messages.append('Max Threads: ' + str(max_threads))
            #print(bcolors.FAIL + "Error: Function Not Implemented Yet." + bcolors.ENDC)
            #return None
            count_files = upload_test(args.upload, bucket_path, max_threads)
            log_messages.append('Number of Files Processed: ' + str(count_files))
        else:
            print(bcolors.FAIL + "Input .test File: " + args.upload + " is not valid.")
            return None
    #Handle all other conditions - too many arguments provided in some cases
    else:
        print(bcolors.FAIL + "Error: You specified too many arguments. Read the README.md file for instructions of how to operate the program." + bcolors.ENDC)
        return None
    
    #Calculate Time Elapsed
    time_elapsed = datetime.now() - start_time 
    
    #Print Time Elapsed
    print('Time elapsed (hh:mm:ss.ms) {}'.format(time_elapsed))
    log_messages.append('Time elapsed (hh:mm:ss.ms) {}'.format(time_elapsed))

    #Write out logging
    print('Writing out log file to ' + log_file)
    if logging == True:
        logger(log_file, log_messages)

def logger(file_path, message_list):
    """
    This function writes out iters of message_list, each on a new line, to file_path. If file_path already exists, the function appends the new message_list
    to the bottom of the file.
    file_path:     type str, absolute or relative path to logging file
    message_list:  type list, of messages (type str), each of which will be separated by a newline character when written out to file_path
    Returns:       None
    """
    old_lines = []
    num_old_lines = 0
    fin = open(file_path, 'r')
    for line in fin.readlines():
        old_lines.append(line.rstrip())
        num_old_lines+=1
    fin.close()
    fout = open(file_path, 'w')
    if num_old_lines > 0:
        for old_line in old_lines:
            fout.write(old_line + '\n')
        fout.write('\n\n')
    for new_line in message_list:
        fout.write(new_line + '\n')
    fout.close()
    return None

def check_dir(directory_path):
    """
    This function checks whether a directory path is valid, and if necessary, adds an additional "/" on the end of the directory path and tries to validate it.
    directory_path: a string of a relative or absolute directory path
    Returns: List [<is_valid>, <dir_path>]
             <is_valid>: True if a valid directory, False if not
             <dir_path>: A potentially corrected directory path, or otherwise None if it was invalid.
    """
    if os.path.isdir(directory_path) == True:
        return [True, directory_path]
    else:
        dir_path = directory_path + "/"
        if os.path.isdir(dir_path) == True:
            return [True, dir_path]
        else:
            print("Invalid Directory: " + directory_path)
            return [False, None]

def check_file(file_path, mode='r'):
    """
    This function checks to see if the file at file_path is valid. This is a simple file system check, and doesn't look at the contents of the file.
    file_path: absolute or relative file path to file to be checked.
    Returns:   True if file is valid, False otherwise.
    """
    try:
        fin = open(file_path, mode)
        fin.close()
        return True
    except OSError:
        return False

def traverse_directory(indir, is_subdir=True, is_files=True, level=1, file_list=[]):
    """
    This function traverses a directory, indir, and has the following options that allow recursion:
    is_subdir: type bool, True to process sub-directories, False to ignore
    is_files:  type bool, True to process files, False to ignore
    level:     type int, the level of directory that it is currently on, because of recursion.
    file_list: type list of [<full_path>, <file_name>]
    Returns:   file_list
    """
    for dirName, subdirList, fileList in os.walk(indir):
        if is_files == True:
            for fname in fileList:
                file_list.append([dirName + "/" + fname, fname])
        for nextdir in subdirList:
            traverse_directory(nextdir, False, True, level=(level + 1), file_list=file_list)
    return file_list

def upload(indir, bucket_path, max_threads):
    """
    This function uploads all subdirectories with files in indir to the S3 bucket.
    indir: string of relative or absolute path to input directory.
    bucket_path: string of S3 bucket in format "s3://bucket-name/"
    max_threads: The maximum number of threads that should be used to download the files from the S3 bucket.
    Returns: None
    """
    count_files = 0
    threads = []
    for full_path, filename in traverse_directory(indir):
        count_files += 1
        threadID = (count_files - 1) % max_threads
        name = "Thread-" + str(threadID)
        this_thread = uploadThread(threadID, name, full_path, filename, bucket_path, count_files)
        wait_timer = 0
        while threading.activeCount() > max_threads:
            wait_timer+=1
        this_thread.start()
        threads.append(this_thread)
    print(bcolors.BOLD + "Processed " + str(count_files) + " files." + bcolors.ENDC)
    bashCommand = "aws s3 ls " + bucket_path
    print(bcolors.WARNING + "Processing AWS S3 Directory Listing: " + bashCommand + bcolors.ENDC)
    os.system(bashCommand)
    for t in threads:
        t.join()
    print("Exiting Main Thread...")
    return count_files

def upload_test(filename, bucket_path, max_threads):
    """
    This function uploads all files, each specified in filename to the S3 bucket_path.
    filename:    type str, the filename or file path to the upload#.test file that contains one file path or file name per line.
    bucket_path: type string of S3 bucket in format "s3://bucket-name/"
    max_threads: type int, the maximum number of threads that should be used to upload the files to the S3 bucket.
    Returns:     None
    """
    fin = open(filename, 'r')
    count_files = 0
    threads = []
    for full_path in fin.readlines():
        count_files+=1
        full_path = full_path.rstrip()
        filename = basename(full_path)
        threadID = (count_files - 1) % max_threads
        name = "Thread-" + str(threadID)
        this_thread = uploadThread(threadID, name, full_path, filename, bucket_path, count_files)
        wait_timer = 0
        while threading.activeCount() > max_threads:
            wait_timer+=1
        this_thread.start()
        threads.append(this_thread)
    fin.close()
    for t in threads:
        t.join()
    print("Exiting Main Thread...")
    return count_files

class uploadThread(threading.Thread):
    """
    This class defines the uploadThread blueprint, of type threading.Thread, which calls do_upload
    to upload one file per thread.
    To Call: uploadThread(threadID, name, full_path, filename, bucket_path, count_files)
    Whereas: threadId:    type int, is the ID of the thread assigned by the calling function
             name:        type str, is the name of the thread assigned by the calling function
             full_path:   type str, is the absolute or relative path to upload the file from
             filename:    type str, is a valid filename, short for full_path
             bucket_path: type str, is a valid S3 bucket path in the format "s3://bucket-name/"
             count_files: type int, is the number of files that have been counted so far in the process
    """
    def __init__(self, threadID, name, full_path, filename, bucket_path, count_files):
       threading.Thread.__init__(self)
       self.threadID = threadID
       self.name = name
       self.full_path = full_path
       self.filename = filename
       self.bucket_path = bucket_path
       self.count_files = count_files
    def run(self):
       print("Starting New Thread")
       do_upload(self.name, self.full_path, self.filename, self.bucket_path, self.count_files)
       print("Exiting " + self.name)


def do_upload(threadName, full_path, filename, bucket_path, count_files):
    """
    This function is called by uploadThread to upload one filename from full_path to bucket_path.
    threadName:  type str, the name of the thread assigned by the calling function
    full_path:   type str, the relative or absolute path to the file to be uploaded
    filename:    type str, the name of the file to be uploaded
    bucket_path: type str, a valid S3 bucket path in the format "s3://bucket-name/"
    count_files: type int, the number of files that have been processed, including the current file
    Returns:     None
    """
    bashCommand = "aws s3 cp " + full_path + " " + bucket_path + filename
    print(bcolors.OKGREEN + "Processing File #" + str(count_files) + ": " + full_path + bcolors.ENDC)
    print(bcolors.OKBLUE + "Running Bash Command: " + bashCommand + bcolors.ENDC)
    sys_call = subprocess.check_output(bashCommand, shell=True)
    print(bcolors.WARNING + "Bash Output: " + "..." + str(sys_call)[-75:-3]  + bcolors.ENDC)
    #os.system(bashCommand)

def download(outdir, bucket_path, max_threads):
    """
    This function downloads all files in from S3 bucket_path to the outdir directory.
    outdir: string of relative or absolute path to output directory.
    bucket_path: string of S3 bucket in format "s3://bucket-name/"
    max_threads: The maximum number of threads that should be used to download the files from the S3 bucket.
    Returns: None
    """
    completed_files = 0
    bashCommand = "aws s3 ls " + bucket_path
    print(bcolors.WARNING + "Processing AWS S3 Directory Listing: " + bashCommand + bcolors.ENDC)
    output = str(subprocess.check_output(bashCommand, shell=True))
    output = output[2:-1]
    output_list = []
    last_char = ""
    this_line = ""
    for char in output.strip():
        if char == 'n' and last_char == '\\':
            output_list.append(this_line[0:-1])
            this_line = ""
            last_char = ""
        else:
            this_line = this_line + char
            last_char = char
    line_count = 0
    count_files = 0
    for line in output_list:
        line_count += 1
        if line_count % 2 == 0:
            print(bcolors.OKBLUE + line + bcolors.ENDC)
        else:
            print(bcolors.OKGREEN + line + bcolors.ENDC)
        filename = line.split()[-1]
        print("Found file: " + filename)
        count_files += 1
        bashCommand = "aws s3 cp " + bucket_path + filename + " " + outdir + filename
        print(bcolors.OKGREEN + "Processing File #" + str(count_files) + ": " + bucket_path + filename + bcolors.ENDC)
        print(bcolors.OKBLUE + "Running Bash Command: " + bashCommand + bcolors.ENDC)
        os.system(bashCommand)

def download_test(filename, outdir, bucket_path, max_threads):
    """
    This function downloads all files, each specified in filename from S3 bucket_path to the outdir directory.
    filename:    type str, the filename or file path to the download#.test file that contains one file path or file name per line.
    outdir:      type string of relative or absolute path to output directory.
    bucket_path: type string of S3 bucket in format "s3://bucket-name/"
    max_threads: type int, the maximum number of threads that should be used to download the files from the S3 bucket.
    Returns:     None
    """
    fin = open(filename, 'r')
    count_files = 0
    threads = []
    for filename in fin.readlines():
        count_files+=1
        filename = filename.rstrip()
        threadID = (count_files - 1) % max_threads
        name = "Thread-" + str(threadID)
        this_thread = downloadThread(threadID, name, outdir, filename, bucket_path, count_files)
        wait_timer = 0
        while threading.activeCount() > max_threads:
            wait_timer+=1
        this_thread.start()
        threads.append(this_thread)
    fin.close()
    for t in threads:
        t.join()
    print("Exiting Main Thread...")
    return count_files

class downloadThread(threading.Thread):
    """
    This class defines the downloadThread blueprint, of type threading.Thread, which calls do_download
    to download one file per thread.
    To Call: downloadThread(threadID, name, outdir, filename, bucket_path, count_files)
    Whereas: threadId:    type int, is the ID of the thread assigned by the calling function
             name:        type str, is the name of the thread assigned by the calling function
             outdir:      type str, is the absolute or relative path to output the downloaded file to
             filename:    type str, is a valid filename on the S3 bucket
             bucket_path: type str, is a valid S3 bucket path in the format "s3://bucket-name/"
             count_files: type int, is the number of files that have been counted so far in the process
    """
    def __init__(self, threadID, name, outdir, filename, bucket_path, count_files):
       threading.Thread.__init__(self)
       self.threadID = threadID
       self.name = name
       self.outdir = outdir
       self.filename = filename
       self.bucket_path = bucket_path
       self.count_files = count_files
    def run(self):
       print("Starting New Thread")
       do_download(self.name, self.outdir, self.filename, self.bucket_path, self.count_files)
       print("Exiting " + self.name)

def do_download(threadName, outdir, filename, bucket_path, count_files):
    """
    This function is called by downloadThread to download one filename from bucket_path to outdir.
    threadName:  type str, the name of the thread assigned by the calling function
    outdir:      type str, the relative or absolute path to the output directory, where the file should
                 be downloaded to
    filename:    type str, the name of the file to be downloaded
    bucket_path: type str, a valid S3 bucket path in the format "s3://bucket-name/"
    count_files: type int, the number of files that have been processed, including the current file
    Returns:     None
    """
    bashCommand = "aws s3 cp " + bucket_path + filename + " " + outdir + filename
    print(bcolors.OKGREEN + "Processing File #" + str(count_files) + ": " + filename + bcolors.ENDC)
    print(bcolors.OKBLUE + "Running Bash Command: " + bashCommand + bcolors.ENDC)
    sys_call = subprocess.check_output(bashCommand, shell=True)
    print(bcolors.WARNING + "Bash Output: " + "..." + str(sys_call)[-75:-3] + bcolors.ENDC)
    #os.system(bashCommand)

if __name__ == "__main__":
    main()
