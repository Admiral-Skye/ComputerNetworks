
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.PrintWriter;
import java.net.InetAddress;
import java.net.MalformedURLException;
import java.net.Socket;
import java.net.URL;
import java.net.UnknownHostException;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;


public class Spider {

	private static int maxPages = 1000; // prevent infinite loop
	// for matching href attr in anchor tags, also for matching the CODE part of the header.
	// from https://examples.javacodegeeks.com/core-java/util/regex/matcher/extract-html-links-with-java-regular-expression-example/
	private static final String HTML_A_TAG_PATTERN = "(?i)<a([^>]+)>(.+?)</a>";
	private static final String HTML_HREF_TAG_PATTERN = "\\s*(?i)href\\s*=\\s*(\"([^\"]*\")|'[^']*'|([^'\">\\s]+))";
	private static final String HTML_CODE_PATTERN = "HTTP\\/1.1\\s*[\\d]+";
	private Pattern pTag,pLink,pCode;
	private Matcher mTag,mLink,mCode;
	
	//For tracking our progress. Taking a breadth first approach
	private Set<String> urlsVisited = new HashSet<String>(); //unique set, make sure we only visit each thing once.
	private List<String> toVisit = new LinkedList<String>(); // preserve order in which we found the urls.

	//values to be returned upon completion
	private String LargestPageUrl = "";
	private long LargestPageSize = -1l;
	private String LastModified = "";
	private Date LastModifiedDate = new Date(1l);

	private List<String> Invalids = new ArrayList<String>();
	private Map<String, String> Redirects = new HashMap<String, String>();// <Source, Target>

	public static void main(String[] args) {
		if (args.length == 0) new Spider("http://3310exp.hopto.org:9780/");
		else {
			if (args.length > 2) maxPages = Integer.parseInt(args[1]);
			new Spider(args[0]);
		}
	}

	public Spider(String url) {
		System.out.println("Starting crawl.\n Starting at: " + url + "\n Max Pages: " + maxPages + "\n");
		String currentUrl = url;
		while (this.urlsVisited.size() < maxPages) { //just in case something dumb happens, exit the loop after visiting a fixed number of pages.
			// scan pages for links and store them

			String html = "";
			System.out.println("Crawling over to " + currentUrl);

			try {
				URL u = new URL(currentUrl);
				int port = u.getPort();
				
				Socket s = new Socket(u.getHost(), port);

				OutputStream theOutput = s.getOutputStream();
				// no auto-flushing
				PrintWriter pw = new PrintWriter(theOutput, false);
				
				// native line endings are uncertain so add them manually
				// HTML Fetching adapted from http://www.cafeaulait.org/course/week12/22.html
				pw.print("GET " + u.getFile() + " HTTP/1.0\r\n");
				pw.print("Accept: text/plain, text/html, text/*\r\n");
				pw.print("\r\n");
				pw.flush();
				
				InputStream in = s.getInputStream();
				InputStreamReader isr = new InputStreamReader(in);
				BufferedReader br = new BufferedReader(isr);
				
				int c;
				while ((c = br.read()) != -1) {
					html += (char) c;
				}
				// end data fetching
				String header;
				if (html.indexOf("<!DOCTYPE") != -1) {
					header = html.substring(0, html.indexOf("<!DOCTYPE"));	
					html = html.substring(html.indexOf("<!DOCTYPE"));				
				} else {
					header = html.substring(0, html.indexOf("<html>"));
					html = html.substring(html.indexOf("<html>"));
				}
				

				//check for redirects
				pCode = Pattern.compile(HTML_CODE_PATTERN);
				mCode = pCode.matcher(header);
				
				int code = -1;
				if (mCode.find()) {
					String match = mCode.group(0); // "HTTP/1.1 DDD"
					code = Integer.parseInt(match.substring(match.length()-3)); // DDD
				}
				
				
				if (code < 300) {
					//success, check last modified
					String lastMod = header.substring(header.indexOf("Last-Modified: ")+"Last-Modified: ".length(), header.indexOf("ETag")).trim();
					//System.out.println(currentUrl + "\n " + header);
					Date last = new Date(lastMod);
					if (last.after(LastModifiedDate)) {
						// more recent
						LastModifiedDate = last;
						LastModified = currentUrl;
					}
				} else if (code >= 300 && code < 400) {
					// redirect
					
					String loc = header.substring(header.indexOf("Location: "), header.indexOf("Content-Length")).trim();
					
					Redirects.put(currentUrl, loc);

				} else if (code >= 400 && code < 500) { // 400, 404, etc
					Invalids.add(currentUrl);
				}
				
				// find other links on the page using some regex
				// adapted from https://www.mkyong.com/regular-expressions/how-to-extract-html-links-with-regular-expression/
				pTag = Pattern.compile(HTML_A_TAG_PATTERN);
				pLink = Pattern.compile(HTML_HREF_TAG_PATTERN);
				
				mTag = pTag.matcher(html);
				mLink = pLink.matcher(html); //apply the black magic here
				
				while (mTag.find()) {

					String href = mTag.group(1); // href="link"

					mLink = pLink.matcher(href);

					while (mLink.find()) {
						
						//NOTE: store ip addresses. rather than the links as causes dupes. Ran out of time and involved a lot of pattern matching
						// maybe use InetAddress.getByName(link) need to omit http
						
						String link = mLink.group(1); // "link"
						link = link.substring(1, link.length()-1); // link
						
						
						toVisit.add(link);

					}

				}
				
				
				// check size of payload. Could probably use the header but whatever
				
				long bytes = html.getBytes().length;
				
				if (bytes > LargestPageSize) {
					LargestPageUrl = currentUrl;
					LargestPageSize = bytes;
				}
				
				s.close();
			} 
			catch (MalformedURLException ex) {
				// also 404? not sure on this one, it was mentioned but i havent seen it thrown yet...
				Invalids.add(currentUrl);
				System.err.println(url + " is not a valid URL");
			}
			catch (UnknownHostException ex) {
				// 404
				Invalids.add(currentUrl);
			}
			catch (IOException ex) {
				// some other read error
				System.err.println(ex);
			}



			if (toVisit.size() == 0) {
				break;
			} else {
				currentUrl = nextLink();
			}
			
			try {
				// be polite and wait two seconds
				Thread.sleep(2000);
			} catch (InterruptedException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		}
		//done, print results

		System.out.println("\n==========================================\nResults:");
		System.out.println("Largest page: " + LargestPageUrl + " at " + LargestPageSize + " bytes");
		System.out.println("Most recently modified page: " + LastModified + " modified at " + LastModifiedDate.toString());
		System.out.println("Invalid links:");
		for (String invalid: Invalids) {
			System.out.println("  " + invalid);
		}

		System.out.println("Redirect links:");
		for (String redirector: Redirects.keySet()) {
			System.out.println("  " + redirector + " redirects to " + Redirects.get(redirector));
		}
		System.out.println("Number of pages visited: " + urlsVisited.size());

	}

	private String nextLink() {
		// Remove all copies of the current link
		String nxt = this.toVisit.remove(0);

		while (urlsVisited.contains(nxt) && !this.toVisit.isEmpty()) {
			nxt = this.toVisit.remove(0); // get next link as we have already been here.
		}
		urlsVisited.add(nxt);
		return nxt;

	}
}
